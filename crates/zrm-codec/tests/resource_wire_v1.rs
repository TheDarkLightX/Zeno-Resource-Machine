//! Cross-language vectors and malformed-input regressions for `ResourceWireV1`.

use std::collections::BTreeSet;

use zrm_codec::{
    ResourceIdDerivationError, ResourceWireDecodeError, ResourceWireEncodeError, ResourceWireV1,
    decode_resource_wire_v1,
};
use zrm_types::{RejectCodeV1, ResourceId};

const ABSENT_VECTOR: &[u8; 595] = include_bytes!("../../../vectors/resource_wire_v1_absent.bin");
const PRESENT_VECTOR: &[u8; 603] = include_bytes!("../../../vectors/resource_wire_v1_present.bin");
const ABSENT_RESOURCE_ID: [u8; 32] = [
    0x41, 0x94, 0x23, 0x6e, 0x9f, 0x6b, 0xf4, 0xb2, 0x7f, 0x2e, 0x06, 0x21, 0x8a, 0xa6, 0x9b, 0x8c,
    0x4a, 0x58, 0xa2, 0xd6, 0x9b, 0xfa, 0xc5, 0xda, 0xeb, 0x72, 0x57, 0x40, 0x20, 0x86, 0xe8, 0xc5,
];
const PRESENT_RESOURCE_ID: [u8; 32] = [
    0x83, 0x58, 0x6e, 0x47, 0x0f, 0x24, 0x59, 0x99, 0xda, 0x41, 0x63, 0xf7, 0x53, 0x41, 0x0c, 0xf4,
    0x66, 0x06, 0xaf, 0xe4, 0xfc, 0x3a, 0x15, 0xb2, 0xc2, 0x0a, 0x61, 0x59, 0xd1, 0x3f, 0x57, 0xb8,
];

#[derive(Debug)]
enum TestError {
    Decode,
    Encode,
    FixtureIndex,
    ResourceId,
}

impl From<ResourceWireDecodeError> for TestError {
    fn from(_: ResourceWireDecodeError) -> Self {
        Self::Decode
    }
}

impl From<ResourceWireEncodeError> for TestError {
    fn from(_: ResourceWireEncodeError) -> Self {
        Self::Encode
    }
}

impl From<ResourceIdDerivationError> for TestError {
    fn from(_: ResourceIdDerivationError) -> Self {
        Self::ResourceId
    }
}

fn fixture(expiry_epoch: Option<u64>) -> ResourceWireV1 {
    ResourceWireV1 {
        machine_id: [0x01; 32],
        domain_id: [0x02; 32],
        application_id: [0x03; 32],
        resource_kind_id: [0x04; 32],
        resource_logic_id: [0x05; 32],
        logic_profile_id: [0x06; 32],
        resource_kind_policy_id: [0x07; 32],
        unit_id: [0x08; 32],
        quantity_atoms: 0x0102_0304_0506_0708_090a_0b0c_0d0e_0f10,
        label_root: [0x0a; 32],
        value_root: [0x0b; 32],
        controller_root: [0x0c; 32],
        policy_root: [0x0d; 32],
        provenance_root: [0x0e; 32],
        nonce: [0x0f; 32],
        created_epoch: 0x0102_0304_0506_0708,
        expiry_epoch,
        flags: 0,
    }
}

fn decode_outcome(bytes: &[u8]) -> Result<(), RejectCodeV1> {
    decode_resource_wire_v1(bytes)
        .map(|_| ())
        .map_err(ResourceWireDecodeError::code)
}

fn set_byte(bytes: &mut [u8], offset: usize, value: u8) -> Result<(), TestError> {
    let Some(slot) = bytes.get_mut(offset) else {
        return Err(TestError::FixtureIndex);
    };
    *slot = value;
    Ok(())
}

fn flip_byte(bytes: &mut [u8], offset: usize) -> Result<(), TestError> {
    let Some(slot) = bytes.get_mut(offset) else {
        return Err(TestError::FixtureIndex);
    };
    *slot ^= 1;
    Ok(())
}

fn range_equals(bytes: &[u8], range: std::ops::Range<usize>, expected: &[u8]) -> bool {
    bytes.get(range) == Some(expected)
}

#[test]
fn absent_expiry_vector_round_trips_and_hashes() -> Result<(), TestError> {
    let expected = fixture(None);
    let encoded = expected.encode()?;
    assert_eq!(encoded.as_slice(), ABSENT_VECTOR);
    assert_eq!(decode_resource_wire_v1(&encoded), Ok(expected.clone()));
    assert_eq!(expected.resource_id()?.into_bytes(), ABSENT_RESOURCE_ID);
    Ok(())
}

#[test]
fn present_expiry_vector_round_trips_and_hashes() -> Result<(), TestError> {
    let expected = fixture(Some(0x1112_1314_1516_1718));
    let encoded = expected.encode()?;
    assert_eq!(encoded.as_slice(), PRESENT_VECTOR);
    assert_eq!(decode_resource_wire_v1(&encoded), Ok(expected.clone()));
    assert_eq!(expected.resource_id()?.into_bytes(), PRESENT_RESOURCE_ID);
    Ok(())
}

#[test]
fn canonical_offsets_and_integers_are_big_endian() {
    assert!(ABSENT_VECTOR.starts_with(&[0x5a, 0x52, 0x4d, 0x31, 0, 1, 0, 1, 0, 18]));
    assert!(range_equals(
        ABSENT_VECTOR,
        320..336,
        &0x0102_0304_0506_0708_090a_0b0c_0d0e_0f10_u128.to_be_bytes()
    ));
    assert!(range_equals(
        ABSENT_VECTOR,
        570..578,
        &0x0102_0304_0506_0708_u64.to_be_bytes()
    ));
    assert!(range_equals(
        PRESENT_VECTOR,
        584..593,
        &[1, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18]
    ));
}

#[test]
fn boundary_atlas_reaches_all_twelve_decoder_outcomes() -> Result<(), TestError> {
    let valid = ABSENT_VECTOR.to_vec();
    let mut cases: Vec<(Vec<u8>, RejectCodeV1)> = Vec::new();

    cases.push((vec![0; 16_385], RejectCodeV1::RESOURCE_WIRE_BYTES));
    cases.push((
        valid.iter().copied().take(9).collect(),
        RejectCodeV1::RESOURCE_WIRE_HEADER,
    ));

    let mut wrong_magic = valid.clone();
    set_byte(&mut wrong_magic, 0, 0)?;
    cases.push((wrong_magic, RejectCodeV1::RESOURCE_WIRE_MAGIC));

    let mut wrong_version = valid.clone();
    set_byte(&mut wrong_version, 5, 2)?;
    cases.push((wrong_version, RejectCodeV1::RESOURCE_WIRE_VERSION));

    let mut wrong_object = valid.clone();
    set_byte(&mut wrong_object, 7, 2)?;
    cases.push((wrong_object, RejectCodeV1::RESOURCE_WIRE_OBJECT));

    let mut wrong_count = valid.clone();
    set_byte(&mut wrong_count, 9, 17)?;
    cases.push((wrong_count, RejectCodeV1::RESOURCE_WIRE_FIELD_COUNT));

    cases.push((
        valid.iter().copied().take(15).collect(),
        RejectCodeV1::RESOURCE_WIRE_FIELD_HEADER,
    ));

    let mut wrong_tag = valid.clone();
    set_byte(&mut wrong_tag, 11, 2)?;
    cases.push((wrong_tag, RejectCodeV1::RESOURCE_WIRE_FIELD_TAG));

    let mut wrong_length = valid.clone();
    set_byte(&mut wrong_length, 15, 31)?;
    cases.push((wrong_length, RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH));

    cases.push((
        valid.iter().copied().take(47).collect(),
        RejectCodeV1::RESOURCE_WIRE_FIELD_VALUE,
    ));

    let mut wrong_option = valid.clone();
    set_byte(&mut wrong_option, 584, 2)?;
    cases.push((wrong_option, RejectCodeV1::RESOURCE_WIRE_OPTION_TAG));

    let mut trailing = valid;
    trailing.push(0);
    cases.push((trailing, RejectCodeV1::RESOURCE_WIRE_TRAILING));

    let mut reached = BTreeSet::new();
    for (bytes, expected) in cases {
        assert_eq!(decode_outcome(&bytes), Err(expected));
        reached.insert(expected.value());
    }
    assert_eq!(reached.len(), 12);
    Ok(())
}

#[test]
fn duplicate_reordered_and_unknown_tags_share_field_tag_reject() -> Result<(), TestError> {
    for replacement in [0x0000_u16, 0x0001, 0x0002, 0xffff] {
        let mut bytes = ABSENT_VECTOR.to_vec();
        let [high, low] = replacement.to_be_bytes();
        set_byte(&mut bytes, 10, high)?;
        set_byte(&mut bytes, 11, low)?;
        if replacement == 0x0001 {
            set_byte(&mut bytes, 48, 0)?;
            set_byte(&mut bytes, 49, 1)?;
            assert_eq!(
                decode_outcome(&bytes),
                Err(RejectCodeV1::RESOURCE_WIRE_FIELD_TAG)
            );
        } else {
            assert_eq!(
                decode_outcome(&bytes),
                Err(RejectCodeV1::RESOURCE_WIRE_FIELD_TAG)
            );
        }
    }
    Ok(())
}

#[test]
fn error_precedence_is_stable_for_multiple_defects() -> Result<(), TestError> {
    let mut oversized_wrong_magic = vec![0; 16_385];
    set_byte(&mut oversized_wrong_magic, 0, 0xff)?;
    assert_eq!(
        decode_outcome(&oversized_wrong_magic),
        Err(RejectCodeV1::RESOURCE_WIRE_BYTES)
    );

    let mut wrong_tag_and_length = ABSENT_VECTOR.to_vec();
    set_byte(&mut wrong_tag_and_length, 11, 2)?;
    set_byte(&mut wrong_tag_and_length, 15, 31)?;
    assert_eq!(
        decode_outcome(&wrong_tag_and_length),
        Err(RejectCodeV1::RESOURCE_WIRE_FIELD_TAG)
    );

    let mut wrong_tag_with_truncated_length =
        ABSENT_VECTOR.iter().copied().take(13).collect::<Vec<_>>();
    set_byte(&mut wrong_tag_with_truncated_length, 11, 2)?;
    assert_eq!(
        decode_outcome(&wrong_tag_with_truncated_length),
        Err(RejectCodeV1::RESOURCE_WIRE_FIELD_HEADER)
    );

    let mut wrong_length_and_truncated = ABSENT_VECTOR.iter().copied().take(20).collect::<Vec<_>>();
    set_byte(&mut wrong_length_and_truncated, 15, 31)?;
    assert_eq!(
        decode_outcome(&wrong_length_and_truncated),
        Err(RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH)
    );

    let mut expiry_value_truncated = ABSENT_VECTOR.iter().copied().take(592).collect::<Vec<_>>();
    set_byte(&mut expiry_value_truncated, 583, 9)?;
    assert_eq!(
        decode_outcome(&expiry_value_truncated),
        Err(RejectCodeV1::RESOURCE_WIRE_FIELD_VALUE)
    );
    Ok(())
}

#[test]
fn complete_header_with_wrong_magic_reaches_magic_guard() {
    let complete_wrong_header = [0_u8; 10];
    assert_eq!(
        decode_outcome(&complete_wrong_header),
        Err(RejectCodeV1::RESOURCE_WIRE_MAGIC)
    );
}

#[test]
fn maximum_bound_distinguishes_trailing_from_oversize() {
    let mut at_limit = ABSENT_VECTOR.to_vec();
    at_limit.resize(16_384, 0);
    assert_eq!(
        decode_outcome(&at_limit),
        Err(RejectCodeV1::RESOURCE_WIRE_TRAILING)
    );

    let mut over_limit = at_limit;
    over_limit.push(0);
    assert_eq!(
        decode_outcome(&over_limit),
        Err(RejectCodeV1::RESOURCE_WIRE_BYTES)
    );
}

#[test]
fn expiry_length_and_tag_cross_product_is_canonical() -> Result<(), TestError> {
    let mut absent_with_present_tag = ABSENT_VECTOR.to_vec();
    set_byte(&mut absent_with_present_tag, 584, 1)?;
    assert_eq!(
        decode_outcome(&absent_with_present_tag),
        Err(RejectCodeV1::RESOURCE_WIRE_OPTION_TAG)
    );

    let mut present_with_absent_tag = PRESENT_VECTOR.to_vec();
    set_byte(&mut present_with_absent_tag, 584, 0)?;
    assert_eq!(
        decode_outcome(&present_with_absent_tag),
        Err(RejectCodeV1::RESOURCE_WIRE_OPTION_TAG)
    );

    let mut invalid_declared_length = ABSENT_VECTOR.to_vec();
    set_byte(&mut invalid_declared_length, 583, 2)?;
    assert_eq!(
        decode_outcome(&invalid_declared_length),
        Err(RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH)
    );
    Ok(())
}

#[test]
fn syntactic_decoder_preserves_semantically_invalid_candidates() -> Result<(), TestError> {
    let candidate = ResourceWireV1 {
        machine_id: [0; 32],
        domain_id: [0; 32],
        application_id: [0; 32],
        resource_kind_id: [0; 32],
        resource_logic_id: [0; 32],
        logic_profile_id: [0; 32],
        resource_kind_policy_id: [0; 32],
        unit_id: [0; 32],
        quantity_atoms: 0,
        label_root: [0; 32],
        value_root: [0; 32],
        controller_root: [0; 32],
        policy_root: [0; 32],
        provenance_root: [0; 32],
        nonce: [0; 32],
        created_epoch: 10,
        expiry_epoch: Some(9),
        flags: u32::MAX,
    };
    let encoded = candidate.encode()?;
    assert_eq!(decode_resource_wire_v1(&encoded), Ok(candidate));
    Ok(())
}

#[test]
fn every_wire_field_changes_resource_id() -> Result<(), TestError> {
    let baseline = fixture(Some(0x1112_1314_1516_1718));
    let baseline_id = baseline.resource_id()?;
    let encoded = baseline.encode()?;
    let value_offsets = [
        16, 54, 92, 130, 168, 206, 244, 282, 320, 342, 380, 418, 456, 494, 532, 570, 585, 599,
    ];

    for offset in value_offsets {
        let mut mutated = encoded.clone();
        flip_byte(&mut mutated, offset)?;
        let decoded = decode_resource_wire_v1(&mutated)?;
        assert_ne!(
            decoded.resource_id()?,
            baseline_id,
            "offset {offset} did not bind"
        );
    }
    Ok(())
}

#[test]
fn deterministic_round_trip_covers_quantity_epoch_and_flags_candidates() -> Result<(), TestError> {
    for (quantity, created_epoch, expiry_epoch, flags) in [
        (0, 0, None, 0),
        (1, 1, Some(1), 1),
        (u128::MAX, u64::MAX, Some(u64::MAX), u32::MAX),
    ] {
        let mut candidate = fixture(expiry_epoch);
        candidate.quantity_atoms = quantity;
        candidate.created_epoch = created_epoch;
        candidate.flags = flags;
        let first = candidate.encode()?;
        let decoded = decode_resource_wire_v1(&first)?;
        let second = decoded.encode()?;
        assert_eq!(first, second);
    }
    Ok(())
}

#[test]
fn resource_id_result_is_a_distinct_opaque_type() -> Result<(), TestError> {
    let resource_id = fixture(None).resource_id()?;
    assert_eq!(
        ResourceId::try_from(resource_id.into_bytes()),
        Ok(resource_id)
    );
    Ok(())
}

#[test]
fn malformed_same_length_bytes_have_no_typed_resource_id_path() -> Result<(), TestError> {
    let mut wrong_magic = ABSENT_VECTOR.to_vec();
    set_byte(&mut wrong_magic, 0, 0)?;

    let mut wrong_tag = ABSENT_VECTOR.to_vec();
    set_byte(&mut wrong_tag, 11, 2)?;

    let mut wrong_length = ABSENT_VECTOR.to_vec();
    set_byte(&mut wrong_length, 15, 31)?;

    let mut wrong_option = ABSENT_VECTOR.to_vec();
    set_byte(&mut wrong_option, 584, 2)?;

    for malformed in [wrong_magic, wrong_tag, wrong_length, wrong_option] {
        assert_eq!(malformed.len(), ABSENT_VECTOR.len());
        assert!(decode_resource_wire_v1(&malformed).is_err());
    }
    Ok(())
}

#[test]
fn resource_wire_debug_redacts_all_fixed_width_candidates_and_nonce() {
    let first = fixture(None);
    let mut second = first.clone();
    second.nonce = [0xa5; 32];

    let first_debug = std::format!("{first:?}");
    let second_debug = std::format!("{second:?}");
    assert_eq!(first_debug, second_debug);
    assert!(first_debug.contains("nonce: [REDACTED]"));
    assert!(first_debug.contains("machine_id: [REDACTED]"));
    assert!(!first_debug.contains("15, 15, 15"));
    assert!(!second_debug.contains("165, 165, 165"));
}
