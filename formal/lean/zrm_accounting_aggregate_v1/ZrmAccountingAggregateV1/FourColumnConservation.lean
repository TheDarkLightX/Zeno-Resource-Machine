import ZrmAccountingAggregateV1.AccountingFoldTree

namespace ZrmAccountingAggregateV1.FourColumnConservation

open ArmZrmFrontier.AccountingStrongAssociativity
open ZrmAccountingAggregateV1.AccountingFoldTree

/-!
The accounting row keeps resource flow and authority flow as separate monotone
limb pairs. Naming follows the candidate four-column schema:

* resource debit = consumed
* resource credit = created
* authority debit = burn
* authority credit = mint

Conservation is stated without subtraction, so it remains meaningful before
the boundary net projection.
-/

structure AggregateRow where
  resource : Limbs
  authority : Limbs
deriving Repr, DecidableEq

def AggregateRow.zero : AggregateRow :=
  ⟨Limbs.zero, Limbs.zero⟩

def AggregateRow.merge (left right : AggregateRow) : AggregateRow :=
  ⟨left.resource.merge right.resource,
    left.authority.merge right.authority⟩

/-- Subtraction-free conservation:
`consumed + minted = created + burned`. -/
def Conserved (row : AggregateRow) : Prop :=
  row.resource.debit + row.authority.credit =
    row.resource.credit + row.authority.debit

instance (row : AggregateRow) : Decidable (Conserved row) :=
  inferInstanceAs (Decidable
    (row.resource.debit + row.authority.credit =
      row.resource.credit + row.authority.debit))

@[simp] theorem AggregateRow.zero_merge (row : AggregateRow) :
    AggregateRow.zero.merge row = row := by
  cases row
  simp [AggregateRow.zero, AggregateRow.merge]

@[simp] theorem AggregateRow.merge_zero (row : AggregateRow) :
    row.merge AggregateRow.zero = row := by
  cases row
  simp [AggregateRow.zero, AggregateRow.merge]

theorem AggregateRow.merge_comm (left right : AggregateRow) :
    left.merge right = right.merge left := by
  cases left with
  | mk leftResource leftAuthority =>
    cases right with
    | mk rightResource rightAuthority =>
      simp only [AggregateRow.merge, AggregateRow.mk.injEq]
      exact ⟨AccountingFoldTree.merge_comm _ _,
        AccountingFoldTree.merge_comm _ _⟩

theorem AggregateRow.merge_assoc
    (first second third : AggregateRow) :
    (first.merge second).merge third =
      first.merge (second.merge third) := by
  cases first
  cases second
  cases third
  simp [AggregateRow.merge, Limbs.merge_assoc]

@[simp] theorem conserved_zero : Conserved AggregateRow.zero := by
  decide

/-- Leaf conservation is closed under pointwise four-column merge. -/
theorem conserved_merge {left right : AggregateRow}
    (leftConserved : Conserved left)
    (rightConserved : Conserved right) :
    Conserved (left.merge right) := by
  cases left with
  | mk leftResource leftAuthority =>
    cases right with
    | mk rightResource rightAuthority =>
      cases leftResource with
      | mk leftConsumed leftCreated =>
        cases leftAuthority with
        | mk leftBurned leftMinted =>
          cases rightResource with
          | mk rightConsumed rightCreated =>
            cases rightAuthority with
            | mk rightBurned rightMinted =>
              simp only [Conserved, AggregateRow.merge, Limbs.merge]
                at leftConserved rightConserved ⊢
              omega

def aggregate : List AggregateRow → AggregateRow
  | [] => AggregateRow.zero
  | row :: rows => row.merge (aggregate rows)

/-- Conservation survives an arbitrary list fold. -/
theorem conserved_aggregate (rows : List AggregateRow)
    (allConserved : ∀ row, row ∈ rows → Conserved row) :
    Conserved (aggregate rows) := by
  induction rows with
  | nil => exact conserved_zero
  | cons row rows ih =>
      apply conserved_merge
      · exact allConserved row (by simp)
      · apply ih
        intro member memberInRows
        exact allConserved member (by simp [memberInRows])

inductive AggregateTree where
  | leaf (row : AggregateRow)
  | node (left right : AggregateTree)
deriving Repr, DecidableEq

def AggregateTree.total : AggregateTree → AggregateRow
  | .leaf row => row
  | .node left right => left.total.merge right.total

def AggregateTree.AllConserved : AggregateTree → Prop
  | .leaf row => Conserved row
  | .node left right => left.AllConserved ∧ right.AllConserved

/-- Conservation survives every nonempty binary aggregation tree. -/
theorem AggregateTree.conserved_total (tree : AggregateTree)
    (leafConserved : tree.AllConserved) :
    Conserved tree.total := by
  induction tree with
  | leaf row =>
      exact leafConserved
  | node left right leftIH rightIH =>
      apply conserved_merge
      · exact leftIH leafConserved.1
      · exact rightIH leafConserved.2

def resourceProjection (row : AggregateRow) : Limbs := row.resource

def projectionLeft : AggregateRow :=
  ⟨Limbs.mk 3 5, Limbs.mk 0 2⟩

def projectionRight : AggregateRow :=
  ⟨Limbs.mk 3 5, Limbs.mk 1 3⟩

/-- Two distinct conserved rows can have the same resource projection: the
two-field view erases distinct nonzero authority flows. Both witnesses have a
nonzero material resource flow, so the collision does not depend on admitting
an all-four-zero aggregate row. -/
theorem resource_projection_collision :
    Conserved projectionLeft ∧
    Conserved projectionRight ∧
    projectionLeft ≠ projectionRight ∧
    resourceProjection projectionLeft =
      resourceProjection projectionRight := by
  decide

theorem resource_projection_not_injective :
    ¬Function.Injective resourceProjection := by
  intro injective
  have rowsEqual : projectionLeft = projectionRight :=
    injective resource_projection_collision.2.2.2
  exact resource_projection_collision.2.2.1 rowsEqual

end ZrmAccountingAggregateV1.FourColumnConservation
