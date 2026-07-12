#![no_main]

use libfuzzer_sys::fuzz_target;
use zrm_policy::fuzz_assert_untrusted_candidate_cost_invariants;

fuzz_target!(|data: &[u8]| {
    fuzz_assert_untrusted_candidate_cost_invariants(data);
});
