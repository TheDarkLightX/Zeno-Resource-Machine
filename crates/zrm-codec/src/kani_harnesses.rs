use zrm_types::RejectCodeV1;

use crate::cursor::Cursor;
use crate::resource_wire_v1::validate_ingress_and_header;

#[kani::proof]
fn cursor_take_is_total_for_bounded_symbolic_length() {
    let bytes: [u8; 16] = kani::any();
    let length: usize = kani::any();
    kani::assume(length <= 32);
    let mut cursor = Cursor::new(&bytes);
    let _result = cursor.take(length, RejectCodeV1::RESOURCE_WIRE_FIELD_VALUE);
}

#[kani::proof]
fn every_short_input_has_deterministic_ingress_precedence() {
    let bytes = [0_u8; 10];
    let length: usize = kani::any();
    kani::assume(length <= 10);
    if let Some(input) = bytes.get(..length) {
        let result = validate_ingress_and_header(input).map_err(|error| error.code());
        if length < 10 {
            assert_eq!(result, Err(RejectCodeV1::RESOURCE_WIRE_HEADER));
        } else {
            assert_eq!(result, Ok(()));
        }
    }
}
