#![no_main]

use libfuzzer_sys::fuzz_target;
use zrm_codec::decode_resource_wire_v1;

fuzz_target!(|data: &[u8]| {
    if let Ok(wire) = decode_resource_wire_v1(data) {
        assert_eq!(wire.encode().as_deref(), Ok(data));
        assert!(wire.resource_id().is_ok());
    }
});
