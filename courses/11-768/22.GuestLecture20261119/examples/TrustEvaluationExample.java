import java.util.List;
import java.util.Locale;

public class TrustEvaluationExample {
    record CaseRuns(int trials, int successes) {}
    record PassRates(double all, double any) {}

    public static void main(String[] args) {
        List<CaseRuns> agentA = List.of(
            new CaseRuns(8, 8), new CaseRuns(8, 8), new CaseRuns(8, 8),
            new CaseRuns(8, 0), new CaseRuns(8, 0));
        List<CaseRuns> agentB = List.of(
            new CaseRuns(8, 5), new CaseRuns(8, 5), new CaseRuns(8, 5),
            new CaseRuns(8, 5), new CaseRuns(8, 4));

        printRates("A", agentA);
        printRates("B", agentB);

        check(rates(agentA, 1), 0.6, 0.6);
        check(rates(agentB, 1), 0.6, 0.6);
        check(rates(agentA, 2), 0.6, 0.6);
        check(rates(agentB, 2), 23.0 / 70, 61.0 / 70);
        check(rates(agentA, 8), 0.6, 0.6);
        check(rates(agentB, 8), 0.0, 1.0);
        System.out.println("All fixed-data checks passed.");
    }

    static PassRates rates(List<CaseRuns> tasks, int picks) {
        double allSuccess = 0;
        double anySuccess = 0;
        for (CaseRuns task : tasks) {
            allSuccess += sameOutcomeProbability(task.successes(), task.trials(), picks);
            anySuccess += 1 - sameOutcomeProbability(
                task.trials() - task.successes(), task.trials(), picks);
        }
        return new PassRates(allSuccess / tasks.size(), anySuccess / tasks.size());
    }

    // Drawing from the observed runs without replacement gives C(matching,k) / C(trials,k).
    static double sameOutcomeProbability(int matching, int trials, int picks) {
        if (picks < 1 || picks > trials || matching < 0 || matching > trials) {
            throw new IllegalArgumentException("Invalid trial counts or sample size");
        }
        if (picks > matching) {
            return 0;
        }
        double probability = 1;
        for (int draw = 0; draw < picks; draw++) {
            probability *= (matching - draw) / (double) (trials - draw);
        }
        return probability;
    }

    static void printRates(String label, List<CaseRuns> tasks) {
        for (int picks : new int[] {1, 2, 8}) {
            PassRates result = rates(tasks, picks);
            System.out.printf(Locale.ROOT, "%s  k=%d  pass^k=%6.2f%%  pass@k=%6.2f%%%n",
                label, picks, result.all() * 100, result.any() * 100);
        }
    }

    static void check(PassRates result, double expectedAll, double expectedAny) {
        if (Math.abs(result.all() - expectedAll) > 1e-12
            || Math.abs(result.any() - expectedAny) > 1e-12) {
            throw new AssertionError("Unexpected pass rates: " + result);
        }
    }
}
