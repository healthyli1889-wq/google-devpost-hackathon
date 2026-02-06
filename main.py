"""Main entry point for CLI-based simulations."""
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from src.config.loader import load_world_config, load_settings
from src.llm.create_llm import create_llm
from src.interaction.turn_based import TurnBasedStrategy
from src.orchestrator.orchestrator import Orchestrator
from src.output.markdown import MarkdownReportGenerator
from src.output.json_log import JSONExporter
import os

load_dotenv()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Simulation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main configs/medieval_market.json
  python -m src.main configs/custom.json --output-dir results/
  python -m src.main configs/test.json --no-json
  python -m src.main configs/test.json --no-images
        """
    )

    parser.add_argument(
        "config",
        type=str,
        help="Path to world configuration JSON file"
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="outputs",
        help="Output directory for reports (default: outputs/)"
    )

    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip markdown report generation"
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Skip JSON log export"
    )

    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip character portrait image generation"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output during simulation"
    )

    return parser.parse_args()


def main():
    """Main simulation runner."""
    args = parse_args()

    print("=" * 60)
    print("Multi-Agent Simulation Framework")
    print("=" * 60)

    print(f"\nLoading configuration from: {args.config}")
    world_config = load_world_config(args.config)
    print(f"  World: {world_config.name}")
    print(f"  Agents: {len(world_config.agents)}")
    print(f"  Duration: {world_config.max_days} days")

    settings = load_settings()

    print("\nInitializing LLM with LangChain...")
    llm = create_llm(
        provider="gemini",
        model_name=os.getenv('GEMINI_MODEL'),
        api_key=os.getenv('GEMINI_API_KEY'),
        temperature=0.7,
        rate_limit_rpm=60
    )
    print("  LangChain LLM ready")

    # Compute timestamp and slug early (needed for image output dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    world_slug = world_config.name.lower().replace(" ", "_")

    # Portrait and scene generation setup
    portrait_results = {}
    image_client = None
    images_enabled = settings.image.enabled and not args.no_images
    images_run_dir = Path("images") / f"{world_slug}_{timestamp}"

    if images_enabled:
        try:
            from src.imaging import NanoBananaClient, PortraitPipeline
            print("\nGenerating character portraits...")
            image_client = NanoBananaClient(
                api_key=os.getenv('GEMINI_API_KEY'),
                model_name=settings.image.image_model,
                min_request_interval=settings.image.min_request_interval,
            )
            pipeline = PortraitPipeline(llm, image_client, images_run_dir)

            agents_data = [
                {"id": a.id, "name": a.name, "identity_script": a.identity_script}
                for a in world_config.agents
            ]
            portrait_results = pipeline.generate_all_portraits(
                agents_data, world_config.world_rules
            )

            success = sum(1 for r in portrait_results.values() if not r.error)
            failed = sum(1 for r in portrait_results.values() if r.error)
            print(f"  Portraits: {success} generated, {failed} failed")
        except Exception as e:
            print(f"  Portrait generation skipped: {e}")

    strategy = TurnBasedStrategy(
        exchanges_per_turn=world_config.exchanges_per_turn
    )

    # Scene generation pipeline (after portraits, before orchestrator)
    scene_pipeline = None
    scene_results_by_day = {}

    if images_enabled and world_config.scene_settings.enabled:
        try:
            from src.imaging import ScenePipeline
            print("\nInitializing scene generation pipeline...")
            if image_client is None:
                from src.imaging import NanoBananaClient
                image_client = NanoBananaClient(
                    api_key=os.getenv('GEMINI_API_KEY'),
                    model_name=settings.image.image_model,
                    min_request_interval=settings.image.min_request_interval,
                )
            scene_pipeline = ScenePipeline(
                llm=llm,
                image_client=image_client,
                output_dir=images_run_dir,
                scene_settings=world_config.scene_settings,
                portrait_results=portrait_results,
                agent_names={a.id: a.name for a in world_config.agents}
            )
            print("  Scene pipeline ready")
        except Exception as e:
            print(f"  Scene pipeline skipped: {e}")

    def on_day_end(day, world_state):
        """Progress callback for scene generation after each day."""
        if scene_pipeline:
            day_conversations = [c for c in world_state.conversations if c.day == day]
            try:
                day_scenes = scene_pipeline.evaluate_and_generate(
                    day=day,
                    conversations=day_conversations,
                    world_rules=world_state.world_rules
                )
                scene_results_by_day[day] = day_scenes
                success = len([s for s in day_scenes if s.image_path])
                print(f"  Scenes generated: {success}")
            except Exception as e:
                print(f"  Scene generation failed: {e}")

    print("\nInitializing orchestrator...")
    orchestrator = Orchestrator(
        world_config=world_config,
        llm=llm,
        interaction_strategy=strategy,
        progress_callback=on_day_end if scene_pipeline else None
    )
    print("  Orchestrator ready")

    print("\n" + "=" * 60)
    print("STARTING SIMULATION")
    print("=" * 60)

    start_time = datetime.now()
    final_state = orchestrator.run_simulation()
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 60)
    print(f"SIMULATION COMPLETE - Duration: {duration:.1f}s")
    print("=" * 60)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_markdown:
        print("\nGenerating markdown report...")
        md_generator = MarkdownReportGenerator(
            final_state,
            portrait_results=portrait_results if portrait_results else None,
            scene_results=scene_results_by_day if scene_results_by_day else None,
        )
        md_path = output_dir / f"{world_slug}_{timestamp}.md"
        md_generator.save_to_file(str(md_path))

    if not args.no_json:
        print("Generating JSON log...")
        json_exporter = JSONExporter(
            final_state,
            scene_results=scene_results_by_day if scene_results_by_day else None,
        )
        json_path = output_dir / f"{world_slug}_{timestamp}.json"
        json_exporter.save_to_file(str(json_path))

    print("\n" + "=" * 60)
    print("ALL DONE!")
    print("=" * 60)
    print(f"\nOutputs saved to: {output_dir.absolute()}/")


if __name__ == "__main__":
    main()
