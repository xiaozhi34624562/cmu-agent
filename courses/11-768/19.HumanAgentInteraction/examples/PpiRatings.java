import java.util.Arrays;
import java.util.Locale;

class PpiRatings {
    record Group(double[] labels, double[] labeledPredictions, double[] unlabeledPredictions) {
        double labelMean() {
            return mean(labels);
        }

        double labeledResidual() {
            return labelMean() - mean(labeledPredictions);
        }

        double estimate(double weight) {
            return labelMean()
                    + weight * (mean(unlabeledPredictions) - mean(labeledPredictions));
        }
    }

    static double mean(double[] scores) {
        return Arrays.stream(scores).average().orElseThrow();
    }

    public static void main(String[] args) {
        var a = new Group(new double[]{4, 5}, new double[]{4.4, 4.8},
                new double[]{3.8, 4.0, 4.2, 4.4});
        var b = new Group(new double[]{3, 4}, new double[]{3.2, 3.8},
                new double[]{3.1, 3.3, 3.5, 3.7});
        System.out.printf(Locale.ROOT, "A: labels %.2f, residual %+.2f, corrected %.2f%n",
                a.labelMean(), a.labeledResidual(), a.estimate(1));
        System.out.printf(Locale.ROOT, "B: labels %.2f, residual %+.2f, corrected %.2f%n",
                b.labelMean(), b.labeledResidual(), b.estimate(1));
        System.out.printf(Locale.ROOT, "A - B: labels %+.2f, predictions %+.2f, corrected %+.2f%n",
                a.estimate(0) - b.estimate(0),
                mean(a.unlabeledPredictions()) - mean(b.unlabeledPredictions()),
                a.estimate(1) - b.estimate(1));
    }
}
