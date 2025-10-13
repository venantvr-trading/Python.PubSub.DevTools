"""
Metrics CLI Commands

Commands pour afficher et exporter les métriques d'événements.
"""
import json

from ...metrics import get_metrics_collector


def format_duration(seconds: float) -> str:
    """Format une durée en format lisible"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    elif seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    else:
        return f"{seconds / 86400:.1f}d"


def format_table(headers, rows):
    """Format des données en table ASCII"""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Create separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    # Print table
    output = []
    output.append(separator)

    # Headers
    header_row = "|"
    for i, header in enumerate(headers):
        header_row += f" {header.ljust(col_widths[i])} |"
    output.append(header_row)
    output.append(separator)

    # Rows
    for row in rows:
        row_str = "|"
        for i, cell in enumerate(row):
            row_str += f" {str(cell).ljust(col_widths[i])} |"
        output.append(row_str)

    output.append(separator)
    return "\n".join(output)


def show_metrics(args):
    """
    Afficher les métriques collectées.

    Usage:
        pubsub-tools metrics show
        pubsub-tools metrics show --last 1h
        pubsub-tools metrics show --format json
    """
    collector = get_metrics_collector()
    summary = collector.get_summary()

    if args.format == 'json':
        print(json.dumps(summary, indent=2))
        return 0

    # Text format
    print("=" * 80)
    print("📊 Event Metrics Summary".center(80))
    print("=" * 80)
    print()

    # Overall stats
    print("Overall Statistics:")
    print(f"  Total Events Published:  {summary['total_events']:,}")
    print(f"  Total Events Processed:  {summary['total_processed']:,}")
    print(f"  Total Events Failed:     {summary['total_failed']:,}")
    print(f"  Error Rate:              {summary['error_rate']:.2f}%")
    print(f"  Avg Processing Time:     {summary['avg_processing_time_ms']:.2f} ms")
    print(f"  Event Rate:              {summary['event_rate_per_sec']:.2f} events/sec")
    print(f"  Uptime:                  {format_duration(summary['uptime_seconds'])}")
    print(f"  Start Time:              {summary['start_time']}")
    print()

    # Top events
    if summary['top_events']:
        print("Top Events:")
        headers = ["Event Type", "Count", "Percentage"]
        rows = []
        for event in summary['top_events']:
            percentage = (event['count'] / summary['total_events'] * 100) if summary['total_events'] > 0 else 0
            rows.append([
                event['event_type'],
                f"{event['count']:,}",
                f"{percentage:.1f}%"
            ])
        print(format_table(headers, rows))
    else:
        print("No events recorded yet.")

    print()
    print("=" * 80)

    return 0


def show_event_stats(args):
    """
    Afficher les statistiques pour un événement spécifique.

    Usage:
        pubsub-tools metrics event OrderCreated
        pubsub-tools metrics event OrderCreated --format json
    """
    collector = get_metrics_collector()
    event_name = args.event_name

    stats = collector.get_event_stats(event_name)

    if stats is None:
        print(f"❌ No statistics found for event: {event_name}")
        return 1

    if args.format == 'json':
        print(json.dumps(stats, indent=2))
        return 0

    # Text format
    print("=" * 80)
    print(f"📊 Statistics for: {event_name}".center(80))
    print("=" * 80)
    print()

    print(f"  Published:   {stats['published']:,}")
    print(f"  Processed:   {stats['processed']:,}")
    print(f"  Failed:      {stats['failed']:,}")
    print(f"  Error Rate:  {stats['error_rate']:.2f}%")
    print()

    if stats['processing_time']:
        print("Processing Time:")
        pt = stats['processing_time']
        print(f"  Count:   {pt['count']:,}")
        print(f"  Min:     {pt['min']:.2f} ms")
        print(f"  Max:     {pt['max']:.2f} ms")
        print(f"  Avg:     {pt['avg']:.2f} ms")
        print(f"  P50:     {pt['p50']:.2f} ms")
        print(f"  P95:     {pt['p95']:.2f} ms")
        print(f"  P99:     {pt['p99']:.2f} ms")

    print()
    print("=" * 80)

    return 0


def show_handler_stats(args):
    """
    Afficher les statistiques pour un handler spécifique.

    Usage:
        pubsub-tools metrics handler handle_order
        pubsub-tools metrics handler handle_order --format json
    """
    collector = get_metrics_collector()
    handler_name = args.handler_name

    stats = collector.get_handler_stats(handler_name)

    if stats['executions'] == 0:
        print(f"❌ No statistics found for handler: {handler_name}")
        return 1

    if args.format == 'json':
        print(json.dumps(stats, indent=2))
        return 0

    # Text format
    print("=" * 80)
    print(f"📊 Statistics for handler: {handler_name}".center(80))
    print("=" * 80)
    print()

    print(f"  Executions:       {stats['executions']:,}")
    print(f"  Avg Duration:     {stats['avg_duration_ms']:.2f} ms")
    print(f"  Min Duration:     {stats['min_duration_ms']:.2f} ms")
    print(f"  Max Duration:     {stats['max_duration_ms']:.2f} ms")

    print()
    print("=" * 80)

    return 0


def export_metrics(args):
    """
    Exporter les métriques dans un fichier.

    Usage:
        pubsub-tools metrics export metrics.json
        pubsub-tools metrics export metrics.json --format json
    """
    collector = get_metrics_collector()
    summary = collector.get_summary()

    output_file = args.output

    try:
        with open(output_file, 'w') as f:
            if args.format == 'json':
                json.dump(summary, f, indent=2)
            else:
                # Default to JSON for export
                json.dump(summary, f, indent=2)

        print(f"✅ Metrics exported to: {output_file}")
        return 0

    except Exception as e:
        print(f"❌ Error exporting metrics: {e}")
        return 1


def reset_metrics(args):
    """
    Réinitialiser toutes les métriques.

    Usage:
        pubsub-tools metrics reset
        pubsub-tools metrics reset --confirm
    """
    if not args.confirm:
        print("⚠️  This will reset ALL metrics data.")
        print("   Use --confirm to proceed.")
        return 1

    collector = get_metrics_collector()
    collector.reset()

    print("✅ All metrics have been reset.")
    return 0


def list_events(args):
    """
    Lister tous les types d'événements enregistrés.

    Usage:
        pubsub-tools metrics list
        pubsub-tools metrics list --format json
    """
    collector = get_metrics_collector()
    all_events = collector.events_published.get_all()

    if not all_events:
        print("No events recorded yet.")
        return 0

    if args.format == 'json':
        print(json.dumps(list(all_events.keys()), indent=2))
        return 0

    # Text format
    print("=" * 80)
    print("📋 Recorded Event Types".center(80))
    print("=" * 80)
    print()

    sorted_events = sorted(all_events.items(), key=lambda x: x[1], reverse=True)

    headers = ["Event Type", "Count"]
    rows = [[event, f"{count:,}"] for event, count in sorted_events]

    print(format_table(headers, rows))
    print()
    print(f"Total: {len(all_events)} event types")
    print("=" * 80)

    return 0


def setup_metrics_parser(subparsers):
    """Setup metrics subcommands"""
    metrics_parser = subparsers.add_parser(
        'metrics',
        help='View and manage event metrics'
    )

    metrics_subparsers = metrics_parser.add_subparsers(dest='metrics_command', help='Metrics command')

    # Show summary
    show_parser = metrics_subparsers.add_parser(
        'show',
        help='Show metrics summary'
    )
    show_parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    show_parser.add_argument(
        '--last',
        help='Show metrics from last duration (e.g., 1h, 30m)'
    )
    show_parser.set_defaults(func=show_metrics)

    # Event stats
    event_parser = metrics_subparsers.add_parser(
        'event',
        help='Show statistics for specific event type'
    )
    event_parser.add_argument(
        'event_name',
        help='Event type name'
    )
    event_parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    event_parser.set_defaults(func=show_event_stats)

    # Handler stats
    handler_parser = metrics_subparsers.add_parser(
        'handler',
        help='Show statistics for specific handler'
    )
    handler_parser.add_argument(
        'handler_name',
        help='Handler name'
    )
    handler_parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    handler_parser.set_defaults(func=show_handler_stats)

    # Export
    export_parser = metrics_subparsers.add_parser(
        'export',
        help='Export metrics to file'
    )
    export_parser.add_argument(
        'output',
        help='Output file path'
    )
    export_parser.add_argument(
        '--format', '-f',
        choices=['json'],
        default='json',
        help='Output format (default: json)'
    )
    export_parser.set_defaults(func=export_metrics)

    # Reset
    reset_parser = metrics_subparsers.add_parser(
        'reset',
        help='Reset all metrics'
    )
    reset_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm reset operation'
    )
    reset_parser.set_defaults(func=reset_metrics)

    # List events
    list_parser = metrics_subparsers.add_parser(
        'list',
        help='List all recorded event types'
    )
    list_parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    list_parser.set_defaults(func=list_events)

    return metrics_parser
