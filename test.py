"""
Performance Tester
Tests latency and I/O of term processing across 3 groups
with proper filtering based on DB state
"""

import json
import time

from server import TermManager


def test_group(manager, group_data, group_name):
    """Test single group and measure performance"""
    print(f"\n{'='*60}")
    print(f"Testing {group_name}")
    print(f"{'='*60}")

    # Measure processing time
    start = time.time()
    result = manager.process_terms(group_data)
    elapsed = time.time() - start

    # Calculate stats
    input_count = len(group_data)
    output_count = len(result)
    filtered_out = input_count - output_count

    print(f"Input terms:      {input_count}")
    print(f"Output terms:     {output_count}")
    print(f"Filtered out:     {filtered_out}")
    print(f"Processing time:  {elapsed*1000:.2f}ms")
    print(f"Throughput:       {input_count/elapsed:.0f} terms/sec")

    return {
        "group": group_name,
        "input": input_count,
        "output": output_count,
        "filtered": filtered_out,
        "time_ms": elapsed * 1000,
        "throughput": input_count / elapsed,
    }


def simulate_human_approval(manager, approval_rate=0.7, disapproval_rate=0.2):
    """Simulate human approving/disapproving pending terms"""
    pending = manager.get_all_pending()

    if not pending:
        print(f"No pending terms to approve/disapprove")
        return

    import random

    approved = int(len(pending) * approval_rate)
    disapproved = int(len(pending) * disapproval_rate)

    # Approve some
    approved_terms = random.sample(pending, min(approved, len(pending)))
    for term in approved_terms:
        manager.update_status(term["term"], "approved")

    # Disapprove remaining selected terms
    remaining_pending = [t for t in pending if t not in approved_terms]
    disapproved_terms = random.sample(
        remaining_pending, min(disapproved, len(remaining_pending))
    )
    for term in disapproved_terms:
        manager.update_status(term["term"], "disapproved")

    print(
        f"Simulated approval: {len(approved_terms)} approved, {len(disapproved_terms)} disapproved"
    )


def get_status_counts(manager):
    """Helper function to get counts of different statuses"""
    stats = manager.get_stats()
    return (
        stats.get("pending", 0),
        stats.get("approved", 0),
        stats.get("disapproved", 0),
    )


def main():
    # Load test data
    print("Loading test data...")
    with open("test_data.json", "r") as f:
        data = json.load(f)

    # Initialize manager
    manager = TermManager()
    manager.clear_all()  # Clean start

    results = []

    # Test Group 1: Add 1000 new terms as pending
    print("\nGROUP 1: Adding 1000 new terms to empty DB (all should pass through)")
    results.append(test_group(manager, data["group1"], "Group 1"))

    # Check initial DB state
    pending, approved, disapproved = get_status_counts(manager)
    print(
        f"DB contains {pending} pending, {approved} approved, {disapproved} disapproved"
    )

    # Simulate human approval of pending terms
    print("\nSimulating human approval of pending terms...")
    simulate_human_approval(manager, approval_rate=0.7, disapproval_rate=0.2)

    # Check DB state after approval
    pending, approved, disapproved = get_status_counts(manager)
    print(
        f"After approval - DB contains {pending} pending, {approved} approved, {disapproved} disapproved"
    )

    # Test Group 2: Send terms again (should see filtering based on DB state)
    print("\nGROUP 2: Sending terms again (some should be filtered based on DB state)")
    results.append(test_group(manager, data["group2"], "Group 2"))

    # Simulate more approvals on remaining pending terms
    print("\nSimulating more human approvals...")
    simulate_human_approval(manager, approval_rate=0.6, disapproval_rate=0.3)

    # Check DB state again
    pending, approved, disapproved = get_status_counts(manager)
    print(
        f"After second approval - DB contains {pending} pending, {approved} approved, {disapproved} disapproved"
    )

    # Test Group 3: Mixed overlap scenario
    print("\nGROUP 3: Sending mixed terms (more filtering expected)")
    results.append(test_group(manager, data["group3"], "Group 3"))

    # Final summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    total_time = sum(r["time_ms"] for r in results)
    avg_throughput = sum(r["throughput"] for r in results) / len(results)

    print(f"Total processing time: {total_time:.2f}ms")
    print(f"Average throughput:    {avg_throughput:.0f} terms/sec")

    for r in results:
        print(f"\n{r['group']}:")
        print(
            f"  Input: {r['input']}, Output: {r['output']}, Filtered: {r['filtered']}"
        )
        print(f"  Time: {r['time_ms']:.2f}ms")

    # Save results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to test_results.json")


if __name__ == "__main__":
    main()
