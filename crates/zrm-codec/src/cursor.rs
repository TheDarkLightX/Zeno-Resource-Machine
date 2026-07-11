use zrm_types::RejectCodeV1;

use crate::ResourceWireDecodeError;

pub(crate) struct Cursor<'a> {
    remaining: &'a [u8],
}

impl<'a> Cursor<'a> {
    pub(crate) const fn new(bytes: &'a [u8]) -> Self {
        Self { remaining: bytes }
    }

    pub(crate) fn take(
        &mut self,
        length: usize,
        reject_code: RejectCodeV1,
    ) -> Result<&'a [u8], ResourceWireDecodeError> {
        let Some((taken, remaining)) = self.remaining.split_at_checked(length) else {
            return Err(ResourceWireDecodeError::new(reject_code));
        };
        self.remaining = remaining;
        Ok(taken)
    }

    pub(crate) fn take_array<const LENGTH: usize>(
        &mut self,
        reject_code: RejectCodeV1,
    ) -> Result<[u8; LENGTH], ResourceWireDecodeError> {
        let bytes = self.take(LENGTH, reject_code)?;
        <[u8; LENGTH]>::try_from(bytes).map_err(|_| ResourceWireDecodeError::new(reject_code))
    }

    pub(crate) fn take_u16(
        &mut self,
        reject_code: RejectCodeV1,
    ) -> Result<u16, ResourceWireDecodeError> {
        self.take_array::<2>(reject_code).map(u16::from_be_bytes)
    }

    pub(crate) fn take_u32(
        &mut self,
        reject_code: RejectCodeV1,
    ) -> Result<u32, ResourceWireDecodeError> {
        self.take_array::<4>(reject_code).map(u32::from_be_bytes)
    }

    pub(crate) const fn is_empty(&self) -> bool {
        self.remaining.is_empty()
    }
}
