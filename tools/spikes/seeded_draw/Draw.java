import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.*;
import java.util.*;

/**
 * SPEC §9.4: do two devices draw the same random occurrence times? Run against each Kotlin stdlib jar
 * and under several default time zones; the runner compares the printed digests.
 *
 * Draws, 1,000 occurrences each:
 *   chronicle  Chronicle's RandomDays seed today (RepeatSchedule.kt:39):
 *              seed = epochSecondUTC(from) * 31 + min * 7 + max; kotlin.random.Random(seed).nextInt(min, max + 1)
 *   factotum   ADR 04's seed: FNV-1a 64 of UTF-8 "itemId|occurrenceDate|kind", fed to kotlin.random.Random
 *   splitmix   the same FNV seed through SplitMix64, written here: no dependency on the Kotlin runtime
 *   window     RANDOM_WINDOW: a minute inside 01:00-04:00 local on the item's days, Europe/Rome, across
 *              the 2027-03-28 spring-forward gap; prints how many drawn times fell in the gap
 * Also prints the lockstep count: two different items with the same start and range drawing the same
 * day under each seed rule.
 */
public class Draw {
    static long fnv1a64(String s) {
        long h = 0xcbf29ce484222325L;
        for (byte b : s.getBytes(StandardCharsets.UTF_8)) { h ^= (b & 0xff); h *= 0x100000001b3L; }
        return h;
    }

    static long splitmix(long[] state) {
        long z = (state[0] += 0x9E3779B97F4A7C15L);
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        return z ^ (z >>> 31);
    }

    static int splitmixBetween(long seed, int from, int untilExclusive) {
        long[] st = {seed};
        long bound = untilExclusive - from;
        // unbiased: reject the top sliver
        long limit = Long.remainderUnsigned(-1L, bound);
        while (true) {
            long r = splitmix(st);
            if (Long.compareUnsigned(r, -1L - limit) <= 0) return from + (int) Long.remainderUnsigned(r, bound);
        }
    }

    static int kotlinBetween(long seed, int from, int untilExclusive) {
        return kotlin.random.RandomKt.Random(seed).nextInt(from, untilExclusive);
    }

    static String digest(StringBuilder sb) throws Exception {
        byte[] d = MessageDigest.getInstance("SHA-256").digest(sb.toString().getBytes(StandardCharsets.UTF_8));
        return HexFormat.of().formatHex(d).substring(0, 16);
    }

    static String chi(int[] c) {
        double e = 25000, x = 0;
        for (int v : c) x += (v - e) * (v - e) / e;
        return String.format("%.2f", x);
    }

    public static void main(String[] args) throws Exception {
        int min = 2, max = 5, n = 1000;
        String item = "01JB8Z3K4Q7M2N5P6R8S9T0V1W", other = "01JB8Z3K4Q7M2N5P6R8S9T0V1X";
        StringBuilder chron = new StringBuilder(), fact = new StringBuilder(), sm = new StringBuilder(), win = new StringBuilder();
        int[] factCounts = new int[max + 1], smCounts = new int[max + 1];
        int lockChron = 0, lockFact = 0, lockSm = 0;
        LocalDateTime from = LocalDateTime.of(2026, 10, 5, 8, 0);
        LocalDate day = from.toLocalDate();
        for (int i = 0; i < n; i++) {
            long cs = from.toEpochSecond(ZoneOffset.UTC) * 31L + min * 7L + max;
            int c = kotlinBetween(cs, min, max + 1);
            chron.append(c).append(',');
            String key = item + "|" + day + "|RANDOM_DAYS", key2 = other + "|" + day + "|RANDOM_DAYS";
            int f = kotlinBetween(fnv1a64(key), min, max + 1), f2 = kotlinBetween(fnv1a64(key2), min, max + 1);
            int s = splitmixBetween(fnv1a64(key), min, max + 1), s2 = splitmixBetween(fnv1a64(key2), min, max + 1);
            fact.append(f).append(','); sm.append(s).append(',');
            factCounts[f]++; smCounts[s]++;
            // Chronicle's seed takes no item: compute the other item's draw from its own (identical) inputs
            long cs2 = from.toEpochSecond(ZoneOffset.UTC) * 31L + min * 7L + max;
            if (kotlinBetween(cs2, min, max + 1) == c) lockChron++;
            if (f == f2) lockFact++;
            if (s == s2) lockSm++;
            from = from.plusDays(c); day = from.toLocalDate();
        }
        // RANDOM_WINDOW across the spring-forward night in Europe/Rome
        ZoneId rome = ZoneId.of("Europe/Rome");
        int inGap = 0;
        LocalDate d0 = LocalDate.of(2027, 3, 20);
        for (int i = 0; i < 14; i++) {
            LocalDate d = d0.plusDays(i);
            for (int k = 0; k < 50; k++) {
                int minute = splitmixBetween(fnv1a64(item + "|" + d + "|RANDOM_WINDOW|" + k), 0, 180);
                LocalDateTime local = d.atTime(1, 0).plusMinutes(minute);
                ZonedDateTime z = local.atZone(rome);
                if (!z.toLocalDateTime().equals(local)) inGap++;
                win.append(z.toInstant().getEpochSecond()).append(',');
            }
        }
        System.out.println("kotlin=" + kotlin.KotlinVersion.CURRENT + " tz=" + ZoneId.systemDefault());
        System.out.println("chronicle=" + digest(chron) + " factotum=" + digest(fact) + " splitmix=" + digest(sm) + " window=" + digest(win));
        System.out.println("lockstep/1000 chronicle=" + lockChron + " factotum=" + lockFact + " splitmix=" + lockSm);
        System.out.println("counts min..max factotum=" + Arrays.toString(Arrays.copyOfRange(factCounts, min, max + 1))
                + " splitmix=" + Arrays.toString(Arrays.copyOfRange(smCounts, min, max + 1)));
        System.out.println("window draws in the DST gap=" + inGap + "/700");
        // uniformity over 100,000 independent keys, 4 outcomes; chi-square vs 25,000 each
        int[] fk = new int[4], sk = new int[4];
        for (int i = 0; i < 100000; i++) {
            long seed = fnv1a64("item" + i + "|" + LocalDate.of(2026, 1, 1).plusDays(i % 3650) + "|RANDOM_DAYS");
            fk[kotlinBetween(seed, 0, 4)]++; sk[splitmixBetween(seed, 0, 4)]++;
        }
        System.out.println("chi2(df=3, 5%=7.81) kotlin=" + chi(fk) + " splitmix=" + chi(sk) + " " + Arrays.toString(fk) + " " + Arrays.toString(sk));
    }
}
