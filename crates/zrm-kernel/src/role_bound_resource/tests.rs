//! Unit tests for local role-binding diagnostics.

use super::IntrinsicRoleBindingErrorV1;

#[test]
fn absent_binding_error_has_a_bounded_identifier_free_diagnostic() {
    assert_eq!(
        std::format!("{}", IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles),
        "intrinsic resource is absent from canonical roles"
    );
}
