import asyncio
from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from predictor.data.canonical_matches import build_canonical_matches, write_build_result
from predictor.data.contracts import SourcePaths
from predictor.data.validation import validate_sources
from predictor.evaluation import (
    BacktestConfig,
    FeatureSearchConfig,
    backtest_dixon_coles,
    backtest_model,
    build_segment_diagnostics,
    compare_feature_configs,
    write_backtest_result,
    write_dixon_coles_backtest_result,
    write_feature_search_result,
    write_segment_diagnostics_result,
)
from predictor.features.build import build_features, write_features_result
from predictor.inference import predict_fixtures, write_fixture_predictions
from predictor.infrastructure.config import get_settings
from predictor.infrastructure.database.bootstrap import build_seed_payload, seed_database
from predictor.infrastructure.database.session import create_session_factory
from predictor.ratings.build import build_ratings, write_ratings_result
from predictor.training import TrainModelConfig, train_model, write_train_result

app = typer.Typer(no_args_is_help=True)
console = Console()


def _paths(data_dir: Path | None) -> tuple[Path, SourcePaths]:
    root = data_dir or get_settings().data_dir
    return root, SourcePaths.from_data_dir(root)


@app.command("validate-data")
def validate_data(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
) -> None:
    _, paths = _paths(data_dir)
    validations = validate_sources(paths)
    table = Table("Source", "Rows", "Status")
    for item in validations:
        table.add_row(item.name, f"{item.rows:,}", "ok" if item.valid else "invalid")
    console.print(table)


@app.command("build-matches")
def build_matches(
    minimum_date: Annotated[
        str,
        typer.Option(help="Minimum match date in YYYY-MM-DD format."),
    ] = "2021-01-01",
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
) -> None:
    root, paths = _paths(data_dir)
    try:
        parsed_minimum_date = date.fromisoformat(minimum_date)
    except ValueError as error:
        raise typer.BadParameter("Use YYYY-MM-DD format.") from error
    result = build_canonical_matches(paths, minimum_date=parsed_minimum_date)
    write_build_result(result, data_dir=root)
    console.print_json(data=result.report)


@app.command("build-ratings")
def build_ratings_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
) -> None:
    root = data_dir or get_settings().data_dir
    result = build_ratings(data_dir=root)
    write_ratings_result(result, data_dir=root)
    console.print_json(data=result.report)


@app.command("build-features")
def build_features_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
) -> None:
    root = data_dir or get_settings().data_dir
    result = build_features(data_dir=root)
    write_features_result(result, data_dir=root)
    console.print_json(data=result.report)


@app.command("train-model")
def train_model_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
    model_dir: Annotated[Path | None, typer.Option(help="Model artifacts directory.")] = None,
    validation_days: Annotated[
        int,
        typer.Option(help="Days reserved for temporal validation."),
    ] = 365,
    alpha: Annotated[
        float,
        typer.Option(help="PoissonRegressor regularization strength."),
    ] = 1.0,
    max_iter: Annotated[
        int,
        typer.Option(help="Maximum iterations for the optimizer."),
    ] = 500,
) -> None:
    settings = get_settings()
    root = data_dir or settings.data_dir
    artifacts_root = model_dir or settings.model_dir
    result = train_model(
        data_dir=root,
        model_dir=artifacts_root,
        config=TrainModelConfig(
            validation_days=validation_days,
            alpha=alpha,
            max_iter=max_iter,
        ),
    )
    write_train_result(result, model_dir=artifacts_root)
    console.print_json(data=result.metadata)


@app.command("predict-fixtures")
def predict_fixtures_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
    model_dir: Annotated[Path | None, typer.Option(help="Model artifacts directory.")] = None,
    model_version: Annotated[
        str | None,
        typer.Option(help="Specific trained model version to use."),
    ] = None,
) -> None:
    settings = get_settings()
    root = data_dir or settings.data_dir
    artifacts_root = model_dir or settings.model_dir
    result = predict_fixtures(
        data_dir=root,
        model_dir=artifacts_root,
        model_version=model_version,
    )
    write_fixture_predictions(
        result,
        data_dir=root,
        model_dir=artifacts_root,
    )
    console.print_json(data=result.metadata)


@app.command("backtest")
def backtest_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
    initial_train_days: Annotated[
        int,
        typer.Option(help="Initial expanding-window training span in days."),
    ] = 730,
    validation_window_days: Annotated[
        int,
        typer.Option(help="Validation block size in days."),
    ] = 180,
    step_days: Annotated[
        int,
        typer.Option(help="How many days to advance between folds."),
    ] = 180,
    alpha: Annotated[
        float,
        typer.Option(help="PoissonRegressor regularization strength."),
    ] = 1.0,
    max_iter: Annotated[
        int,
        typer.Option(help="Maximum iterations for the optimizer."),
    ] = 500,
) -> None:
    root = data_dir or get_settings().data_dir
    result = backtest_model(
        data_dir=root,
        config=BacktestConfig(
            initial_train_days=initial_train_days,
            validation_window_days=validation_window_days,
            step_days=step_days,
            alpha=alpha,
            max_iter=max_iter,
        ),
    )
    write_backtest_result(result, data_dir=root)
    console.print_json(data=result.report)


def _parse_csv_ints(raw: str) -> list[int]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return [int(item) for item in values]


def _parse_csv_floats(raw: str) -> list[float]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return [float(item) for item in values]


@app.command("compare-feature-configs")
def compare_feature_configs_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
    half_life_days: Annotated[
        str,
        typer.Option(help="Comma-separated half-life values in days."),
    ] = "180,365,540",
    history_years: Annotated[
        str,
        typer.Option(help="Comma-separated history window values in years."),
    ] = "3,5,8",
    initial_train_days: Annotated[
        int,
        typer.Option(help="Initial expanding-window training span in days."),
    ] = 730,
    validation_window_days: Annotated[
        int,
        typer.Option(help="Validation block size in days."),
    ] = 180,
    step_days: Annotated[
        int,
        typer.Option(help="How many days to advance between folds."),
    ] = 180,
    alpha: Annotated[
        float,
        typer.Option(help="PoissonRegressor regularization strength."),
    ] = 1.0,
    max_iter: Annotated[
        int,
        typer.Option(help="Maximum iterations for the optimizer."),
    ] = 500,
) -> None:
    root = data_dir or get_settings().data_dir
    result = compare_feature_configs(
        data_dir=root,
        config=FeatureSearchConfig(
            half_life_days=tuple(_parse_csv_floats(half_life_days)),
            history_years=tuple(_parse_csv_ints(history_years)),
            backtest=BacktestConfig(
                initial_train_days=initial_train_days,
                validation_window_days=validation_window_days,
                step_days=step_days,
                alpha=alpha,
                max_iter=max_iter,
            ),
        ),
    )
    write_feature_search_result(result, data_dir=root)
    console.print_json(data=result.report)


@app.command("backtest-dixon-coles")
def backtest_dixon_coles_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
    initial_train_days: Annotated[
        int,
        typer.Option(help="Initial expanding-window training span in days."),
    ] = 730,
    validation_window_days: Annotated[
        int,
        typer.Option(help="Validation block size in days."),
    ] = 180,
    step_days: Annotated[
        int,
        typer.Option(help="How many days to advance between folds."),
    ] = 180,
    alpha: Annotated[
        float,
        typer.Option(help="PoissonRegressor regularization strength."),
    ] = 1.0,
    max_iter: Annotated[
        int,
        typer.Option(help="Maximum iterations for the optimizer."),
    ] = 500,
) -> None:
    root = data_dir or get_settings().data_dir
    result = backtest_dixon_coles(
        data_dir=root,
        config=BacktestConfig(
            initial_train_days=initial_train_days,
            validation_window_days=validation_window_days,
            step_days=step_days,
            alpha=alpha,
            max_iter=max_iter,
        ),
    )
    write_dixon_coles_backtest_result(result, data_dir=root)
    console.print_json(data=result.report)


@app.command("segment-diagnostics")
def segment_diagnostics_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
) -> None:
    root = data_dir or get_settings().data_dir
    result = build_segment_diagnostics(data_dir=root)
    write_segment_diagnostics_result(result, data_dir=root)
    console.print_json(data=result.report)


@app.command("seed-database")
def seed_database_command(
    data_dir: Annotated[Path | None, typer.Option(help="Data directory.")] = None,
    model_dir: Annotated[Path | None, typer.Option(help="Model artifacts directory.")] = None,
) -> None:
    settings = get_settings()
    root = data_dir or settings.data_dir
    artifacts_root = model_dir or settings.model_dir
    payload = build_seed_payload(data_dir=root, model_dir=artifacts_root)
    factory = create_session_factory(settings)
    report = asyncio.run(seed_database(factory=factory, payload=payload))
    console.print_json(data=report)


if __name__ == "__main__":
    app()
