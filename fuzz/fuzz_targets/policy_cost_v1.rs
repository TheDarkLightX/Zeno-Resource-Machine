#![no_main]

use libfuzzer_sys::fuzz_target;
use zrm_policy::{
    ProofModeV1, VerifierCostErrorV1, VerifierCostModelCandidateV1, VerifierCostModelV1,
    VerifierCostRowCandidateV1, VerifierCostRowV1, VerifierPolicyCandidateV1, VerifierPolicyV1,
    fuzz_candidate_quote_units, fuzz_candidate_reservation_units,
};
use zrm_types::{BackendFamilyId, VerifierCostRowsRoot};

const REQUIRED_BYTES: usize = 88;

fn read_u64(data: &[u8], offset: usize) -> Option<u64> {
    let end = offset.checked_add(8)?;
    let bytes: [u8; 8] = data.get(offset..end)?.try_into().ok()?;
    Some(u64::from_be_bytes(bytes))
}

fn nonzero<T>(byte: u8) -> Option<T>
where
    T: TryFrom<[u8; 32]>,
{
    T::try_from([byte; 32]).ok()
}

fn verifier_policy(
    backend_family_id: BackendFamilyId,
    max_artifact_bytes: u64,
    max_public_input_bytes: u64,
    max_public_output_bytes: u64,
    max_verifier_cost_units: u64,
) -> Option<VerifierPolicyV1> {
    VerifierPolicyV1::try_from(VerifierPolicyCandidateV1 {
        schema_version: 1,
        verifier_policy_id: nonzero(3)?,
        machine_id: nonzero(4)?,
        domain_id: nonzero(5)?,
        backend_family_id,
        verifier_id: nonzero(6)?,
        program_or_key_digest: nonzero(7)?,
        artifact_codec_id: nonzero(8)?,
        statement_schema_root: nonzero(9)?,
        journal_schema_root: nonzero(10)?,
        proof_parameter_root: nonzero(11)?,
        proof_mode: ProofModeV1::Production,
        coverage_claims_root: nonzero(12)?,
        non_claims_root: nonzero(13)?,
        trusted_computing_base_root: nonzero(14)?,
        verifier_cost_model_id: nonzero(15)?,
        max_verifier_cost_units,
        max_artifact_bytes,
        max_public_input_bytes,
        max_public_output_bytes,
        validity_start_epoch: 0,
        validity_end_epoch: u64::MAX,
    })
    .ok()
}

fuzz_target!(|data: &[u8]| {
    if data.len() < REQUIRED_BYTES {
        return;
    }
    let Some(backend) = BackendFamilyId::try_from([1; 32]).ok() else {
        return;
    };
    let Some(rows_root) = VerifierCostRowsRoot::try_from([2; 32]).ok() else {
        return;
    };
    let Some(base_units) = read_u64(data, 0) else {
        return;
    };
    let Some(artifact_byte_units) = read_u64(data, 8) else {
        return;
    };
    let Some(statement_byte_units) = read_u64(data, 16) else {
        return;
    };
    let Some(reserved_output_byte_units) = read_u64(data, 24) else {
        return;
    };
    let Some(artifact_max) = read_u64(data, 32) else {
        return;
    };
    let Some(statement_max) = read_u64(data, 40) else {
        return;
    };
    let Some(output_max) = read_u64(data, 48) else {
        return;
    };
    let Some(model_cap) = read_u64(data, 56) else {
        return;
    };
    let Some(verifier_cap) = read_u64(data, 64) else {
        return;
    };
    let Some(artifact_candidate) = read_u64(data, 72) else {
        return;
    };
    let Some(statement_candidate) = read_u64(data, 80) else {
        return;
    };

    let row = VerifierCostRowV1::new(VerifierCostRowCandidateV1 {
        backend_family_id: backend,
        base_units,
        artifact_byte_units,
        statement_byte_units,
        reserved_output_byte_units,
    });
    let Ok(model) = VerifierCostModelV1::try_from(VerifierCostModelCandidateV1 {
        schema_version: 1,
        rows_root,
        max_charge_units: model_cap,
    }) else {
        return;
    };
    let Some(policy) = verifier_policy(
        backend,
        artifact_max,
        statement_max,
        output_max,
        verifier_cap,
    ) else {
        return;
    };

    // Keep raw lengths for explicit bound-reject coverage and precedence.
    let first = fuzz_candidate_quote_units(
        &model,
        &row,
        &policy,
        [artifact_candidate, statement_candidate],
    );
    let second = fuzz_candidate_quote_units(
        &model,
        &row,
        &policy,
        [artifact_candidate, statement_candidate],
    );
    assert_eq!(first, second);
    if artifact_candidate > artifact_max {
        assert_eq!(first, Err(VerifierCostErrorV1::ArtifactBytesExceeded));
    } else if statement_candidate > statement_max {
        assert_eq!(first, Err(VerifierCostErrorV1::PublicInputBytesExceeded));
    }

    // Compare a bounded actual quote with the policy-maximal reservation quote.
    let bounded = fuzz_candidate_quote_units(
        &model,
        &row,
        &policy,
        [
            artifact_candidate.min(artifact_max),
            statement_candidate.min(statement_max),
        ],
    );
    let reservation = fuzz_candidate_reservation_units(&model, &row, &policy);
    if let (Ok(actual), Ok(reserved)) = (bounded, reservation) {
        assert!(actual <= reserved);
        assert!(actual <= model_cap);
        assert!(actual <= verifier_cap);
    }
});
