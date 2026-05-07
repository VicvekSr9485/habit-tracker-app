"""Command-line interface for the habit tracker.

Built on `Click <https://click.palletsprojects.com/>`_. The module
instantiates a single :class:`SQLiteStorage` against ``habits.db`` in
the working directory and a matching :class:`HabitManager`; tests
replace these with in-memory equivalents using ``monkeypatch``.

Run ``python -m cli.controller --help`` to see every command.
"""

import click
from datetime import datetime
from tabulate import tabulate
from typing import Optional

from core.habit_manager import HabitManager
from storage.sqlite_storage import SQLiteStorage
from analytics import analytics


# Initialize manager
storage = SQLiteStorage("habits.db")
manager = HabitManager(storage)


@click.group()
def cli():
    """Habit Tracker — track your habits and build streaks.

    Top-level command group. Run any subcommand with ``--help`` for
    its individual options.
    """
    pass


@cli.command()
@click.option("--name", prompt="Habit name", help="Name of the habit")
@click.option("--description", prompt="Description", help="Description of the habit")
@click.option(
    "--periodicity",
    type=click.Choice(["daily", "weekly"]),
    prompt="Periodicity",
    help="How often to track (daily or weekly)"
)
def create(name: str, description: str, periodicity: str):
    """Create a new habit and print its assigned ID.

    All three options are prompted interactively when omitted.
    """
    try:
        habit = manager.create_habit(name, description, periodicity)
        click.echo(click.style(f"\n✓ Habit created successfully!", fg="green"))
        click.echo(f"  ID: {habit.id}")
        click.echo(f"  Name: {habit.name}")
        click.echo(f"  Periodicity: {habit.periodicity}")
    except ValueError as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg="red"))


@cli.command()
@click.option("--periodicity", type=click.Choice(["daily", "weekly"]), help="Filter by periodicity")
def list(periodicity: Optional[str]):
    """Print habits as a table, optionally filtered by periodicity."""
    if periodicity:
        habits = manager.get_habits_by_periodicity(periodicity)
        title = f"{periodicity.capitalize()} Habits"
    else:
        habits = manager.get_all_habits()
        title = "All Habits"
    
    if not habits:
        click.echo(click.style(f"\nNo {periodicity or ''} habits found.", fg="yellow"))
        return
    
    # Prepare table data
    table_data = []
    for habit in habits:
        status = "✓" if not habit.is_broken() else "✗"
        status_color = "green" if not habit.is_broken() else "red"
        
        table_data.append([
            habit.id,
            habit.name,
            habit.periodicity,
            f"{habit.get_current_streak()} days" if habit.periodicity == "daily" else f"{habit.get_current_streak()} weeks",
            len(habit.completions),
            click.style(status, fg=status_color)
        ])
    
    click.echo(f"\n{title}")
    click.echo("=" * 80)
    click.echo(tabulate(
        table_data,
        headers=["ID", "Name", "Period", "Current Streak", "Completions", "Status"],
        tablefmt="simple"
    ))
    click.echo()


@cli.command()
@click.argument("habit_id", type=int)
def complete(habit_id: int):
    """Mark a habit complete for the current period.

    Prints a warning when the habit was already completed for this
    period (the manager's idempotent dedupe).
    """
    habit = manager.get_habit(habit_id)
    
    if not habit:
        click.echo(click.style(f"\n✗ Habit with ID {habit_id} not found.", fg="red"))
        return
    
    success = manager.complete_habit(habit_id)
    
    if success:
        # Reload to get updated streak
        habit = manager.get_habit(habit_id)
        click.echo(click.style(f"\n✓ Habit '{habit.name}' completed!", fg="green"))
        click.echo(f"  Current streak: {habit.get_current_streak()}")
        click.echo(f"  Longest streak: {habit.get_longest_streak()}")
    else:
        click.echo(click.style(
            f"\n⚠ Habit already completed for this period.",
            fg="yellow"
        ))


@cli.command()
@click.argument("habit_id", type=int)
def delete(habit_id: int):
    """Delete a habit after an interactive confirmation prompt."""
    habit = manager.get_habit(habit_id)
    
    if not habit:
        click.echo(click.style(f"\n✗ Habit with ID {habit_id} not found.", fg="red"))
        return
    
    if click.confirm(f"Are you sure you want to delete '{habit.name}'?"):
        success = manager.delete_habit(habit_id)
        if success:
            click.echo(click.style(f"\n✓ Habit deleted successfully.", fg="green"))
        else:
            click.echo(click.style(f"\n✗ Failed to delete habit.", fg="red"))
    else:
        click.echo("\nCancelled.")


@cli.command()
@click.argument("habit_id", type=int)
def info(habit_id: int):
    """Show full details for one habit, including recent completions."""
    habit = manager.get_habit(habit_id)
    
    if not habit:
        click.echo(click.style(f"\n✗ Habit with ID {habit_id} not found.", fg="red"))
        return
    
    click.echo(f"\n{habit.name}")
    click.echo("=" * 80)
    click.echo(f"Description: {habit.description}")
    click.echo(f"Periodicity: {habit.periodicity}")
    click.echo(f"Created: {habit.created_at.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"Current Streak: {habit.get_current_streak()}")
    click.echo(f"Longest Streak: {habit.get_longest_streak()}")
    click.echo(f"Total Completions: {len(habit.completions)}")
    click.echo(f"Status: {'Active' if not habit.is_broken() else 'Broken'}")
    
    if habit.completions:
        click.echo("\nRecent Completions:")
        recent = sorted(habit.completions, reverse=True)[:5]
        for comp in recent:
            click.echo(f"  • {comp.strftime('%Y-%m-%d %H:%M')}")
    
    click.echo()


@cli.command()
def analyze():
    """Print a one-screen analytics summary for every tracked habit."""
    habits = manager.get_all_habits()
    
    if not habits:
        click.echo(click.style("\nNo habits to analyze.", fg="yellow"))
        return
    
    summary = analytics.get_analytics_summary(habits)
    
    click.echo("\nHabit Analytics Summary")
    click.echo("=" * 80)
    click.echo(f"Total Habits: {summary['total_habits']}")
    click.echo(f"Daily Habits: {summary['daily_habits']}")
    click.echo(f"Weekly Habits: {summary['weekly_habits']}")
    click.echo(f"Total Completions: {summary['total_completions']}")
    click.echo(f"Average Current Streak: {summary['average_streak']}")
    
    if summary['longest_streak_habit']:
        click.echo(click.style(
            f"\n🏆 Longest Streak: {summary['longest_streak_habit']} "
            f"({summary['longest_streak_days']} periods)",
            fg="yellow", bold=True
        ))
    
    # Show struggling habits
    struggling = analytics.get_struggling_habits(habits, 30)
    if struggling:
        click.echo("\n⚠ Struggling Habits (last 30 days):")
        for h in struggling:
            click.echo(f"  • {h['name']}: {h['completion_rate']}% "
                      f"({h['actual']}/{h['expected']} completions)")
    
    click.echo()


@cli.command()
def longest():
    """Print the habit holding the all-time longest streak."""
    habits = manager.get_all_habits()
    
    if not habits:
        click.echo(click.style("\nNo habits found.", fg="yellow"))
        return
    
    habit_name, streak = analytics.get_longest_streak_all(habits)
    
    if habit_name:
        click.echo(click.style(
            f"\n🏆 Longest Streak: {habit_name} ({streak} periods)",
            fg="yellow", bold=True
        ))
    else:
        click.echo(click.style("\nNo streaks found.", fg="yellow"))


if __name__ == "__main__":
    cli()