using System;
using System.Collections.Generic;

namespace CaeJob;

/// <summary>
/// A recommendation for one host's planned solver jobs. This does not reserve
/// CPUs, change affinity, configure a solver, or enforce a utilization limit.
/// </summary>
public sealed class SolverThreadPlan
{
    public const int MaximumPlannedJobs = 1024;
    public int AvailableLogicalProcessors { get; }
    public int TotalThreadBudget { get; }
    public bool IsAutomatic { get; }
    public IReadOnlyList<int> ThreadsPerJob { get; }

    private SolverThreadPlan(int available, int budget, bool automatic, int[] allocations)
    {
        AvailableLogicalProcessors = available;
        TotalThreadBudget = budget;
        IsAutomatic = automatic;
        ThreadsPerJob = Array.AsReadOnly(allocations);
    }

    /// <param name="availableLogicalProcessors">CPUs available to the execution process.</param>
    /// <param name="plannedConcurrentJobs">Number of jobs sharing this budget, at most 1024.</param>
    /// <param name="manualTotalBudget">Optional total across all planned jobs, not per job.</param>
    public static SolverThreadPlan Create(int availableLogicalProcessors,
        int plannedConcurrentJobs = 1, int? manualTotalBudget = null)
    {
        if (availableLogicalProcessors < 1)
            throw new ArgumentOutOfRangeException(nameof(availableLogicalProcessors), "At least one available CPU is required.");
        if (plannedConcurrentJobs < 1 || plannedConcurrentJobs > MaximumPlannedJobs)
            throw new ArgumentOutOfRangeException(nameof(plannedConcurrentJobs), "Planned jobs must be in [1,1024].");
        if (manualTotalBudget.HasValue &&
            (manualTotalBudget.Value < 1 || manualTotalBudget.Value > availableLogicalProcessors))
            throw new ArgumentOutOfRangeException(nameof(manualTotalBudget), "Manual total budget must be between one and the available CPU count.");

        int budget = manualTotalBudget ?? Math.Max(1, (int)((long)availableLogicalProcessors * 3 / 4));
        if (plannedConcurrentJobs > budget)
            throw new ArgumentOutOfRangeException(nameof(plannedConcurrentJobs), "More simultaneous jobs than the thread budget; reduce concurrency or choose a larger manual budget.");
        int[] allocations = new int[plannedConcurrentJobs];
        for (int i = 0; i < allocations.Length; i++)
            allocations[i] = budget / plannedConcurrentJobs + (i < budget % plannedConcurrentJobs ? 1 : 0);
        return new SolverThreadPlan(availableLogicalProcessors, budget, !manualTotalBudget.HasValue, allocations);
    }
}
