from __future__ import annotations

import asyncio
import functools
import math
import time
import typing
from concurrent.futures import CancelledError, Future, ProcessPoolExecutor
from pathlib import Path

from randovania.cli import cli_lib
from randovania.interface_common import sleep_inhibitor
from randovania.resolver.exceptions import GenerationFailure, ImpossibleForSolver

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction

    from randovania.layout.generator_parameters import GeneratorParameters


def get_generator_params(base_params: GeneratorParameters, seed_number: int) -> GeneratorParameters:
    from randovania.layout.permalink import GeneratorParameters

    assert isinstance(base_params, GeneratorParameters)

    return GeneratorParameters(
        seed_number=seed_number,
        spoiler=True,
        development=base_params.development,
        presets=base_params.presets,
    )


def batch_distribute_helper(
    base_params: GeneratorParameters,
    seed_number: int,
    timeout: int,
    validate: bool,
    output_dir: Path,
) -> float:
    from randovania.generator import generator

    permalink = get_generator_params(base_params, seed_number)

    start_time = time.perf_counter()
    description = asyncio.run(
        generator.generate_and_validate_description(
            generator_params=permalink,
            status_update=None,
            validate_after_generation=validate,
            timeout=timeout,
            attempts=0,
        )
    )
    delta_time = time.perf_counter() - start_time

    description.save_to_file(output_dir.joinpath(f"{seed_number}.{description.file_extension()}"))
    return delta_time


def batch_distribute_command_logic(args: Namespace) -> None:
    from randovania.layout.permalink import Permalink

    finished_count = 0
    impossible_count = 0
    impossible_seeds = []
    failure_count = 0
    failure_seeds = []

    timeout: int = args.timeout
    validate: bool = args.validate

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_count = args.seed_count
    num_digits = math.ceil(math.log10(seed_count + 1))
    number_format = "[{0:" + str(num_digits) + "d}/{1}] "
    base_permalink = Permalink.from_str(args.permalink)
    base_params = base_permalink.parameters

    def get_permalink_text(seed: int) -> str:
        return Permalink.from_parameters(get_generator_params(base_params, seed)).as_base64_str

    def report_update(seed: int, msg: str) -> None:
        nonlocal finished_count
        finished_count += 1
        front = number_format.format(finished_count, seed_count)
        print(f"{front} [ {get_permalink_text(seed)} ] {msg}")

    all_futures: list[Future] = []

    def with_result(seed: int, r: Future) -> None:
        try:
            report_update(seed, f"Finished seed in {r.result()} seconds.")
        except ImpossibleForSolver as e:
            report_update(seed, f"Failed to generate seed: {e}")
            nonlocal impossible_count
            impossible_count += 1
            nonlocal impossible_seeds
            impossible_seeds.append(get_permalink_text(seed))
        except GenerationFailure as e:
            report_update(seed, f"Failed to generate seed: {e}\nReason: {e.source}")
            nonlocal failure_count
            failure_count += 1
            nonlocal failure_seeds
            failure_seeds.append(get_permalink_text(seed))
        except CancelledError:
            nonlocal finished_count
            finished_count += 1
        except Exception as e:
            report_update(seed, f"Failed to generate seed: {e} ({type(e)})")
        except KeyboardInterrupt:
            report_update(seed, "Interrupt requested.")
            for f in all_futures:
                f.cancel()

    try:
        with sleep_inhibitor.get_inhibitor():
            with ProcessPoolExecutor(max_workers=args.process_count) as pool:
                for seed_number in range(base_params.seed_number, base_params.seed_number + args.seed_count):
                    result = pool.submit(
                        batch_distribute_helper,
                        base_params,
                        seed_number,
                        timeout,
                        validate,
                        output_dir,
                    )
                    result.add_done_callback(functools.partial(with_result, seed_number))
                    all_futures.append(result)

    except KeyboardInterrupt:
        pass

    print("Generation Failed: " + str(failure_count) + " " + str(failure_seeds))
    print("Impossible for Solver: " + str(impossible_count) + " " + str(impossible_seeds))


def add_batch_distribute_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("batch-distribute", help="Generate multiple layouts in parallel")

    parser.add_argument("permalink", type=str, help="The permalink to use")
    parser.add_argument("--process-count", type=int, help="How many processes to use. Defaults to CPU count.")
    parser.add_argument(
        "--timeout", type=int, default=90, help="How many seconds to wait before timing out a generation/validation."
    )
    cli_lib.add_validate_argument(parser)
    parser.add_argument("seed_count", type=int, help="How many layouts to generate.")
    parser.add_argument("output_dir", type=Path, help="Where to place the seed logs.")
    parser.set_defaults(func=batch_distribute_command_logic)
