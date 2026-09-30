import java.time.LocalDate;
/** Ten independent 100,000-draw batches per generator; counts chi-square failures at 5% (7.81, df=3).
 *  At a true 5% level about 0.5 of 10 batches fail by chance. */
public class Uniform {
    public static void main(String[] a) {
        int kFail = 0, sFail = 0;
        StringBuilder ks = new StringBuilder(), ss = new StringBuilder();
        for (int b = 0; b < 10; b++) {
            int[] fk = new int[4], sk = new int[4];
            for (int i = 0; i < 100000; i++) {
                long seed = Draw.fnv1a64("batch" + b + "-item" + i + "|" + LocalDate.of(2026, 1, 1).plusDays(i % 3650) + "|RANDOM_DAYS");
                fk[Draw.kotlinBetween(seed, 0, 4)]++; sk[Draw.splitmixBetween(seed, 0, 4)]++;
            }
            double xk = chi(fk), xs = chi(sk);
            if (xk > 7.81) kFail++; if (xs > 7.81) sFail++;
            ks.append(String.format("%.1f ", xk)); ss.append(String.format("%.1f ", xs));
        }
        System.out.println("kotlin   chi2: " + ks + " failures " + kFail + "/10");
        System.out.println("splitmix chi2: " + ss + " failures " + sFail + "/10");
    }
    static double chi(int[] c) { double e = 25000, x = 0; for (int v : c) x += (v - e) * (v - e) / e; return x; }
}
