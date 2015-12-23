import flat_concave
import examples
import numpy as np
import bounds


def check(t, alpha, eps, delta, beta, samples_size=0):
    range_end = 2**t
    if samples_size == 0:
        samples_size = int(bounds.step6_n2_bound(range_end, eps, alpha, beta))
    data_center = np.random.uniform(range_end/3, range_end/3*2)
    data = examples.get_random_data(samples_size, pivot=data_center)
    data = sorted(filter(lambda x: 0 <= x <= range_end, data))
    maximum_quality = examples.min_max_maximum_quality(data, (0, range_end))
    quality_result_lower_bound = maximum_quality * (1-alpha)
    try:
        result = flat_concave.evaluate(data, range_end, examples.quality_minmax, maximum_quality, alpha, eps, delta,
                                       examples.min_max_intervals_bounding, examples.min_max_maximum_quality)
        result_quality = examples.quality_minmax(data, result)
    except ValueError:
        # result = -1
        result_quality = -1
    return result_quality != -1, result_quality >= quality_result_lower_bound, result_quality-quality_result_lower_bound

range_end_exponent = 20
my_alpha = 0.2
my_eps = 0.1
my_delta = 2**-20
my_beta = 0.01

samples = 1000

iters = 20
checks = []
for i in xrange(iters):
    print i
    checks.append(check(range_end_exponent, my_alpha, my_eps, my_delta, my_beta, samples))

did_not_fail = sum(i[0] for i in checks)
good_quality = sum(i[1] for i in checks)
min_quality = min(i[2] for i in checks)
print "proportion of times Adist returned a value: %.2f" % (did_not_fail/float(iters))
print "proportion of times we got good quality: %.2f" % (did_not_fail/float(iters))
print "minimum distance from quality-lower-bound: %d" % min_quality