#![no_main]

use libfuzzer_sys::fuzz_target;
use zrm_codec::ResourceWireV1;
use zrm_kernel::{
    CanonicalResourceRolesV1, IntrinsicResourceV1, IntrinsicRoleBindingErrorV1,
    ResourceRoleListsCandidateV1, ResourceRoleV1,
};
use zrm_policy::PolicyLimitsV1;
use zrm_types::ResourceId;

const INPUT_BYTES: usize = 21;
const MUTABLE_FIELD_COUNT: u8 = 17;

fn quantity(data: &[u8; INPUT_BYTES]) -> u128 {
    let mut bytes = [0_u8; 16];
    bytes.copy_from_slice(&data[5..]);
    u128::from_be_bytes(bytes)
}

fn wire(marker: u8, quantity_atoms: u128) -> ResourceWireV1 {
    ResourceWireV1 {
        machine_id: [1; 32],
        domain_id: [2; 32],
        application_id: [3; 32],
        resource_kind_id: [4; 32],
        resource_logic_id: [5; 32],
        logic_profile_id: [6; 32],
        resource_kind_policy_id: [7; 32],
        unit_id: [8; 32],
        quantity_atoms,
        label_root: [10; 32],
        value_root: [11; 32],
        controller_root: [12; 32],
        policy_root: [13; 32],
        provenance_root: [14; 32],
        nonce: [marker; 32],
        created_epoch: 1,
        expiry_epoch: Some(2),
        flags: 0,
    }
}

fn mutate_valid_field(resource: &mut ResourceWireV1, selector: u8) {
    match selector % MUTABLE_FIELD_COUNT {
        0 => resource.machine_id = [101; 32],
        1 => resource.domain_id = [102; 32],
        2 => resource.application_id = [103; 32],
        3 => resource.resource_kind_id = [104; 32],
        4 => resource.resource_logic_id = [105; 32],
        5 => resource.logic_profile_id = [106; 32],
        6 => resource.resource_kind_policy_id = [107; 32],
        7 => resource.unit_id = [108; 32],
        8 => resource.quantity_atoms = !resource.quantity_atoms,
        9 => resource.label_root = [110; 32],
        10 => resource.value_root = [111; 32],
        11 => resource.controller_root = [112; 32],
        12 => resource.policy_root = [113; 32],
        13 => resource.provenance_root = [114; 32],
        14 => resource.nonce[0] ^= 1,
        15 => resource.created_epoch = 2,
        _ => resource.expiry_epoch = None,
    }
}

fn must_intrinsic(resource: ResourceWireV1, context: &str) -> IntrinsicResourceV1 {
    match IntrinsicResourceV1::try_from(resource) {
        Ok(resource) => resource,
        Err(error) => panic!("internally valid {context} resource failed construction: {error:?}"),
    }
}

fn peer_wire(marker: u8, quantity_atoms: u128) -> ResourceWireV1 {
    let mut resource = wire(marker, quantity_atoms);
    resource.application_id = [marker.wrapping_add(128); 32];
    resource
}

struct OwnedRoleLists {
    consumed: Vec<ResourceId>,
    referenced: Vec<ResourceId>,
    created: Vec<ResourceId>,
}

impl OwnedRoleLists {
    fn push(&mut self, role: ResourceRoleV1, resource_id: ResourceId) {
        match role {
            ResourceRoleV1::Consumed => self.consumed.push(resource_id),
            ResourceRoleV1::Referenced => self.referenced.push(resource_id),
            ResourceRoleV1::Created => self.created.push(resource_id),
        }
    }

    fn permute(&mut self, selector: u8) {
        permute(&mut self.consumed, selector);
        permute(&mut self.referenced, selector);
        permute(&mut self.created, selector);
    }

    fn candidate(&self) -> ResourceRoleListsCandidateV1<'_> {
        ResourceRoleListsCandidateV1 {
            consumed: &self.consumed,
            referenced: &self.referenced,
            created: &self.created,
        }
    }

    fn for_role(&self, role: ResourceRoleV1) -> &[ResourceId] {
        match role {
            ResourceRoleV1::Consumed => &self.consumed,
            ResourceRoleV1::Referenced => &self.referenced,
            ResourceRoleV1::Created => &self.created,
        }
    }

    fn contains(&self, resource_id: &ResourceId) -> bool {
        self.consumed.contains(resource_id)
            || self.referenced.contains(resource_id)
            || self.created.contains(resource_id)
    }
}

fn selected_role(selector: u8) -> Option<ResourceRoleV1> {
    match selector & 3 {
        1 => Some(ResourceRoleV1::Consumed),
        2 => Some(ResourceRoleV1::Referenced),
        3 => Some(ResourceRoleV1::Created),
        _ => None,
    }
}

fn permute(resources: &mut [ResourceId], selector: u8) {
    match selector % 3 {
        1 => resources.reverse(),
        2 if resources.len() > 1 => resources.rotate_left(1),
        _ => {}
    }
}

fn expected_ordinal(resources: &[ResourceId], target: ResourceId) -> u32 {
    let count = resources
        .iter()
        .filter(|candidate| **candidate < target)
        .count();
    match count.try_into() {
        Ok(ordinal) => ordinal,
        Err(_) => panic!("bounded role-list count did not fit in u32"),
    }
}

fuzz_target!(|data: &[u8]| {
    let Ok(data) = <&[u8; INPUT_BYTES]>::try_from(data) else {
        return;
    };
    let target_marker = data[4].saturating_add(1);
    let target_wire = wire(target_marker, quantity(data));
    let base_target = match IntrinsicResourceV1::try_from_wire(&target_wire) {
        Ok(resource) => resource,
        Err(error) => panic!("internally valid target resource failed construction: {error:?}"),
    };
    let target_role = selected_role(data[0]);
    let stale_body = data[2] & 1 == 1;
    let target_id_for_roles = base_target.resource_id();

    let other_consumed = must_intrinsic(peer_wire(41, 1), "consumed peer");
    let other_referenced = must_intrinsic(peer_wire(42, 2), "referenced peer");
    let other_created = must_intrinsic(peer_wire(43, 3), "created peer");
    let other_peer = must_intrinsic(peer_wire(44, 4), "same-role peer");
    let other_ids = [
        other_consumed.resource_id(),
        other_referenced.resource_id(),
        other_created.resource_id(),
        other_peer.resource_id(),
    ];
    assert!(
        !other_ids.contains(&target_id_for_roles),
        "different target and peer bodies produced the same resource ID"
    );

    let [consumed_id, referenced_id, created_id, peer_id] = other_ids;
    let mut role_lists = OwnedRoleLists {
        consumed: vec![consumed_id],
        referenced: vec![referenced_id],
        created: vec![created_id],
    };
    let peer_role = match target_role {
        Some(role) => role,
        None => ResourceRoleV1::Consumed,
    };
    role_lists.push(peer_role, peer_id);
    if let Some(role) = target_role {
        role_lists.push(role, target_id_for_roles);
    }
    role_lists.permute(data[1]);

    let roles = match CanonicalResourceRolesV1::try_new(
        role_lists.candidate(),
        PolicyLimitsV1::strict_default(),
    ) {
        Ok(roles) => roles,
        Err(error) => panic!("internally valid role partition failed construction: {error:?}"),
    };

    let resource = if stale_body {
        let mut changed_wire = target_wire.clone();
        mutate_valid_field(&mut changed_wire, data[3]);
        assert_ne!(
            changed_wire, target_wire,
            "selected valid-field mutation unexpectedly made no change"
        );
        let changed = must_intrinsic(changed_wire, "mutated target");
        assert_ne!(
            changed.resource_id(),
            target_id_for_roles,
            "different target bodies produced the same resource ID"
        );
        assert!(
            !role_lists.contains(&changed.resource_id()),
            "different mutated and peer bodies produced the same resource ID"
        );
        changed
    } else {
        base_target
    };

    let consumed_snapshot = roles.consumed().to_vec();
    let referenced_snapshot = roles.referenced().to_vec();
    let created_snapshot = roles.created().to_vec();
    let first = roles.bind_intrinsic(&resource);
    let replay = roles.bind_intrinsic(&resource);
    assert_eq!(first, replay);

    if stale_body || target_role.is_none() {
        assert_eq!(
            first,
            Err(IntrinsicRoleBindingErrorV1::ResourceAbsentFromRoles)
        );
    } else if let Some(role) = target_role {
        let candidates = role_lists.for_role(role);
        let ordinal = expected_ordinal(candidates, target_id_for_roles);
        let Ok(bound) = first else {
            panic!("present intrinsic resource failed role binding")
        };
        assert_eq!(bound.resource(), &resource);
        assert_eq!(bound.resource_id(), target_id_for_roles);
        assert_eq!(bound.role(), role);
        assert_eq!(bound.ordinal(), ordinal);
    }

    assert_eq!(roles.consumed(), consumed_snapshot);
    assert_eq!(roles.referenced(), referenced_snapshot);
    assert_eq!(roles.created(), created_snapshot);
});
