use alloc::vec::Vec;

use zrm_crypto::derive_resource_id_from_canonical_wire;
use zrm_types::{
    MAX_RESOURCE_BYTES, RESOURCE_WIRE_V1_ABSENT_EXPIRY_BYTES,
    RESOURCE_WIRE_V1_PRESENT_EXPIRY_BYTES, RejectCodeV1, ResourceId,
};

use crate::cursor::Cursor;
use crate::{ResourceIdDerivationError, ResourceWireDecodeError, ResourceWireEncodeError};

const MAGIC: [u8; 4] = *b"ZRM1";
const SCHEMA_VERSION: u16 = 1;
const OBJECT_TAG: u16 = 1;
const FIELD_COUNT: u16 = 18;
const HEADER_BYTES: usize = 10;

/// Syntactically canonical version-one resource wire value.
///
/// Every 32-byte field, quantity, epoch, nonce, and flag remains an inert wire
/// candidate. Later work packages own semantic nonzero, quantity, epoch,
/// policy, and flag validation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResourceWireV1 {
    /// Candidate machine identifier bytes.
    pub machine_id: [u8; 32],
    /// Candidate domain identifier bytes.
    pub domain_id: [u8; 32],
    /// Candidate application identifier bytes.
    pub application_id: [u8; 32],
    /// Candidate resource-kind identifier bytes.
    pub resource_kind_id: [u8; 32],
    /// Candidate resource-logic identifier bytes.
    pub resource_logic_id: [u8; 32],
    /// Candidate logic-profile identifier bytes.
    pub logic_profile_id: [u8; 32],
    /// Candidate resource-kind-policy identifier bytes.
    pub resource_kind_policy_id: [u8; 32],
    /// Candidate unit identifier bytes.
    pub unit_id: [u8; 32],
    /// Candidate nonnegative quantity atoms.
    pub quantity_atoms: u128,
    /// Candidate label commitment bytes.
    pub label_root: [u8; 32],
    /// Candidate value commitment bytes.
    pub value_root: [u8; 32],
    /// Candidate controller-root bytes.
    pub controller_root: [u8; 32],
    /// Candidate policy-root bytes.
    pub policy_root: [u8; 32],
    /// Candidate provenance-root bytes.
    pub provenance_root: [u8; 32],
    /// Candidate resource nonce bytes.
    pub nonce: [u8; 32],
    /// Candidate creation epoch.
    pub created_epoch: u64,
    /// Candidate optional expiry epoch.
    pub expiry_epoch: Option<u64>,
    /// Candidate raw version-one flags. Semantic construction requires zero.
    pub flags: u32,
}

impl ResourceWireV1 {
    /// Encodes the exact canonical 595-byte or 603-byte wire form.
    ///
    /// # Errors
    ///
    /// Returns [`ResourceWireEncodeError::AllocationFailed`] if the bounded
    /// output allocation cannot be reserved.
    pub fn encode(&self) -> Result<Vec<u8>, ResourceWireEncodeError> {
        let encoded_length = if self.expiry_epoch.is_some() {
            RESOURCE_WIRE_V1_PRESENT_EXPIRY_BYTES
        } else {
            RESOURCE_WIRE_V1_ABSENT_EXPIRY_BYTES
        };
        let mut output = Vec::new();
        output
            .try_reserve_exact(encoded_length)
            .map_err(|_| ResourceWireEncodeError::AllocationFailed)?;
        append_header(&mut output);
        append_fixed_field(&mut output, 0x0001, &self.machine_id)?;
        append_fixed_field(&mut output, 0x0002, &self.domain_id)?;
        append_fixed_field(&mut output, 0x0003, &self.application_id)?;
        append_fixed_field(&mut output, 0x0004, &self.resource_kind_id)?;
        append_fixed_field(&mut output, 0x0005, &self.resource_logic_id)?;
        append_fixed_field(&mut output, 0x0006, &self.logic_profile_id)?;
        append_fixed_field(&mut output, 0x0007, &self.resource_kind_policy_id)?;
        append_fixed_field(&mut output, 0x0008, &self.unit_id)?;
        append_fixed_field(&mut output, 0x0009, &self.quantity_atoms.to_be_bytes())?;
        append_fixed_field(&mut output, 0x000a, &self.label_root)?;
        append_fixed_field(&mut output, 0x000b, &self.value_root)?;
        append_fixed_field(&mut output, 0x000c, &self.controller_root)?;
        append_fixed_field(&mut output, 0x000d, &self.policy_root)?;
        append_fixed_field(&mut output, 0x000e, &self.provenance_root)?;
        append_fixed_field(&mut output, 0x000f, &self.nonce)?;
        append_fixed_field(&mut output, 0x0010, &self.created_epoch.to_be_bytes())?;
        append_expiry_field(&mut output, self.expiry_epoch);
        append_fixed_field(&mut output, 0x0012, &self.flags.to_be_bytes())?;
        Ok(output)
    }

    /// Derives an inert `ResourceId` from this syntactically canonical value.
    ///
    /// Later semantic validation must recompute the ID before granting any
    /// resource authority.
    ///
    /// # Errors
    ///
    /// Returns a typed encoding or closed hash-framing error.
    pub fn resource_id(&self) -> Result<ResourceId, ResourceIdDerivationError> {
        let wire = self.encode().map_err(ResourceIdDerivationError::Encode)?;
        derive_resource_id_from_canonical_wire(&wire).map_err(ResourceIdDerivationError::Hash)
    }
}

/// Strictly decodes one bounded `ResourceWireV1` value.
///
/// The function is deterministic, performs no allocation, and preserves the
/// normative error precedence. Successful output is syntactic data, not a
/// semantically validated resource.
///
/// # Errors
///
/// Returns a stable [`ResourceWireDecodeError`] for the first applicable WP1
/// reject condition.
pub fn decode_resource_wire_v1(bytes: &[u8]) -> Result<ResourceWireV1, ResourceWireDecodeError> {
    validate_ingress_and_header(bytes)?;
    let mut cursor = Cursor::new(bytes);
    parse_header(&mut cursor)?;

    let resource = ResourceWireV1 {
        machine_id: read_fixed_field::<32>(&mut cursor, 0x0001)?,
        domain_id: read_fixed_field::<32>(&mut cursor, 0x0002)?,
        application_id: read_fixed_field::<32>(&mut cursor, 0x0003)?,
        resource_kind_id: read_fixed_field::<32>(&mut cursor, 0x0004)?,
        resource_logic_id: read_fixed_field::<32>(&mut cursor, 0x0005)?,
        logic_profile_id: read_fixed_field::<32>(&mut cursor, 0x0006)?,
        resource_kind_policy_id: read_fixed_field::<32>(&mut cursor, 0x0007)?,
        unit_id: read_fixed_field::<32>(&mut cursor, 0x0008)?,
        quantity_atoms: u128::from_be_bytes(read_fixed_field::<16>(&mut cursor, 0x0009)?),
        label_root: read_fixed_field::<32>(&mut cursor, 0x000a)?,
        value_root: read_fixed_field::<32>(&mut cursor, 0x000b)?,
        controller_root: read_fixed_field::<32>(&mut cursor, 0x000c)?,
        policy_root: read_fixed_field::<32>(&mut cursor, 0x000d)?,
        provenance_root: read_fixed_field::<32>(&mut cursor, 0x000e)?,
        nonce: read_fixed_field::<32>(&mut cursor, 0x000f)?,
        created_epoch: u64::from_be_bytes(read_fixed_field::<8>(&mut cursor, 0x0010)?),
        expiry_epoch: read_expiry_field(&mut cursor)?,
        flags: u32::from_be_bytes(read_fixed_field::<4>(&mut cursor, 0x0012)?),
    };

    if !cursor.is_empty() {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_TRAILING,
        ));
    }

    Ok(resource)
}

pub(crate) fn validate_ingress_and_header(bytes: &[u8]) -> Result<(), ResourceWireDecodeError> {
    if bytes.len() > MAX_RESOURCE_BYTES {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_BYTES,
        ));
    }
    if bytes.get(..HEADER_BYTES).is_none() {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_HEADER,
        ));
    }
    Ok(())
}

fn parse_header(cursor: &mut Cursor<'_>) -> Result<(), ResourceWireDecodeError> {
    let header_error = RejectCodeV1::RESOURCE_WIRE_HEADER;
    if cursor.take_array::<4>(header_error)? != MAGIC {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_MAGIC,
        ));
    }
    if cursor.take_u16(header_error)? != SCHEMA_VERSION {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_VERSION,
        ));
    }
    if cursor.take_u16(header_error)? != OBJECT_TAG {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_OBJECT,
        ));
    }
    if cursor.take_u16(header_error)? != FIELD_COUNT {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_FIELD_COUNT,
        ));
    }
    Ok(())
}

fn read_field_header(
    cursor: &mut Cursor<'_>,
    expected_tag: u16,
) -> Result<u32, ResourceWireDecodeError> {
    let tag = cursor.take_u16(RejectCodeV1::RESOURCE_WIRE_FIELD_HEADER)?;
    let length = cursor.take_u32(RejectCodeV1::RESOURCE_WIRE_FIELD_HEADER)?;
    if tag != expected_tag {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_FIELD_TAG,
        ));
    }
    Ok(length)
}

fn read_fixed_field<const LENGTH: usize>(
    cursor: &mut Cursor<'_>,
    expected_tag: u16,
) -> Result<[u8; LENGTH], ResourceWireDecodeError> {
    let declared_length = read_field_header(cursor, expected_tag)?;
    let expected_length = u32::try_from(LENGTH)
        .map_err(|_| ResourceWireDecodeError::new(RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH))?;
    if declared_length != expected_length {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH,
        ));
    }
    cursor.take_array::<LENGTH>(RejectCodeV1::RESOURCE_WIRE_FIELD_VALUE)
}

fn read_expiry_field(cursor: &mut Cursor<'_>) -> Result<Option<u64>, ResourceWireDecodeError> {
    let declared_length = read_field_header(cursor, 0x0011)?;
    if declared_length != 1 && declared_length != 9 {
        return Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH,
        ));
    }
    let value_length = usize::try_from(declared_length)
        .map_err(|_| ResourceWireDecodeError::new(RejectCodeV1::RESOURCE_WIRE_FIELD_LENGTH))?;
    let value = cursor.take(value_length, RejectCodeV1::RESOURCE_WIRE_FIELD_VALUE)?;
    match value {
        [0] => Ok(None),
        [
            1,
            byte_0,
            byte_1,
            byte_2,
            byte_3,
            byte_4,
            byte_5,
            byte_6,
            byte_7,
        ] => Ok(Some(u64::from_be_bytes([
            *byte_0, *byte_1, *byte_2, *byte_3, *byte_4, *byte_5, *byte_6, *byte_7,
        ]))),
        _ => Err(ResourceWireDecodeError::new(
            RejectCodeV1::RESOURCE_WIRE_OPTION_TAG,
        )),
    }
}

fn append_header(output: &mut Vec<u8>) {
    output.extend_from_slice(&MAGIC);
    output.extend_from_slice(&SCHEMA_VERSION.to_be_bytes());
    output.extend_from_slice(&OBJECT_TAG.to_be_bytes());
    output.extend_from_slice(&FIELD_COUNT.to_be_bytes());
}

fn append_fixed_field<const LENGTH: usize>(
    output: &mut Vec<u8>,
    tag: u16,
    value: &[u8; LENGTH],
) -> Result<(), ResourceWireEncodeError> {
    let length = u32::try_from(LENGTH).map_err(|_| ResourceWireEncodeError::LengthOverflow)?;
    output.extend_from_slice(&tag.to_be_bytes());
    output.extend_from_slice(&length.to_be_bytes());
    output.extend_from_slice(value);
    Ok(())
}

fn append_expiry_field(output: &mut Vec<u8>, expiry_epoch: Option<u64>) {
    output.extend_from_slice(&0x0011_u16.to_be_bytes());
    match expiry_epoch {
        None => {
            output.extend_from_slice(&1_u32.to_be_bytes());
            output.push(0);
        }
        Some(epoch) => {
            output.extend_from_slice(&9_u32.to_be_bytes());
            output.push(1);
            output.extend_from_slice(&epoch.to_be_bytes());
        }
    }
}
