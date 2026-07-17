import ArmZrmFrontier.AccountingStrongAssociativity
import ArmZrmFrontier.ExactCoverage

namespace ZrmAccountingAggregateV1.AccountingFoldTree

open ArmZrmFrontier.AccountingStrongAssociativity
open ArmZrmFrontier.ExactCoverage

/-!
This module lifts the local three-input accounting result to arbitrary lists
and nonempty binary merge trees. It deliberately reasons about the abstract
monotone limb model only; implementation refinement remains a separate task.
-/

@[simp] theorem zero_merge (value : Limbs) :
    Limbs.zero.merge value = value := by
  cases value
  simp [Limbs.zero, Limbs.merge]

@[simp] theorem merge_zero (value : Limbs) :
    value.merge Limbs.zero = value := by
  cases value
  simp [Limbs.zero, Limbs.merge]

theorem merge_comm (left right : Limbs) :
    left.merge right = right.merge left := by
  cases left
  cases right
  simp [Limbs.merge, Nat.add_comm]

@[simp] theorem zero_within (bound : Nat) :
    Limbs.zero.within bound := by
  simp [Limbs.zero, Limbs.within]

/-- A bounded monotone total implies that its left contribution is bounded. -/
theorem within_left_of_merge {bound : Nat} {left right : Limbs}
    (fits : (left.merge right).within bound) :
    left.within bound := by
  cases left with
  | mk leftDebit leftCredit =>
    cases right with
    | mk rightDebit rightCredit =>
      simp only [Limbs.merge, Limbs.within] at fits ⊢
      omega

/-- A bounded monotone total implies that its right contribution is bounded. -/
theorem within_right_of_merge {bound : Nat} {left right : Limbs}
    (fits : (left.merge right).within bound) :
    right.within bound := by
  cases left with
  | mk leftDebit leftCredit =>
    cases right with
    | mk rightDebit rightCredit =>
      simp only [Limbs.merge, Limbs.within] at fits ⊢
      omega

/-- The unbounded accounting total of a row list. -/
def aggregate : List Limbs → Limbs
  | [] => Limbs.zero
  | row :: rows => row.merge (aggregate rows)

theorem aggregate_append (left right : List Limbs) :
    aggregate (left ++ right) = (aggregate left).merge (aggregate right) := by
  induction left with
  | nil => simp [aggregate]
  | cons row rows ih =>
      simp only [List.cons_append, aggregate]
      rw [ih, Limbs.merge_assoc]

/-- Exact multiset coverage preserves the accounting total, including
multiplicity. This is intentionally narrower than transcript equality: the
accounting algebra is commutative, while journals remain ordered elsewhere. -/
theorem aggregate_eq_of_exact_coverage
    {left right : List Limbs}
    (coverage : CoversExactly left right) :
    aggregate left = aggregate right := by
  induction coverage with
  | nil => rfl
  | cons row coverage ih =>
      simp only [aggregate]
      rw [ih]
  | swap first second rows =>
      simp only [aggregate]
      rw [← Limbs.merge_assoc, merge_comm second first,
        Limbs.merge_assoc]
  | trans first second firstIH secondIH =>
      exact firstIH.trans secondIH

/-- A checked right fold. It checks every recursive subtotal as well as the
complete total. -/
def checkedAggregate (bound : Nat) : List Limbs → Option Limbs
  | [] => some Limbs.zero
  | row :: rows =>
      (checkedAggregate bound rows).bind fun subtotal =>
        checkedMerge bound row subtotal

/-- A checked list fold has a complete characterization: it succeeds exactly
when the final monotone total fits, and then returns that exact total. Thus
there are no hidden intermediate-overflow cases. -/
theorem checkedAggregate_spec (bound : Nat) (rows : List Limbs) :
    checkedAggregate bound rows =
      if (aggregate rows).within bound
      then some (aggregate rows)
      else none := by
  induction rows with
  | nil => simp [checkedAggregate, aggregate]
  | cons row rows ih =>
      simp only [checkedAggregate, aggregate]
      rw [ih]
      by_cases totalFits : (row.merge (aggregate rows)).within bound
      · have tailFits : (aggregate rows).within bound :=
          within_right_of_merge totalFits
        simp [tailFits, checkedMerge, totalFits]
      · by_cases tailFits : (aggregate rows).within bound
        · simp [tailFits, checkedMerge, totalFits]
        · simp [tailFits, totalFits]

theorem checkedAggregate_eq_some_iff
    (bound : Nat) (rows : List Limbs) (result : Limbs) :
    checkedAggregate bound rows = some result ↔
      (aggregate rows).within bound ∧ result = aggregate rows := by
  rw [checkedAggregate_spec]
  by_cases fits : (aggregate rows).within bound <;>
    simp [fits, eq_comm]

theorem checkedAggregate_eq_none_iff
    (bound : Nat) (rows : List Limbs) :
    checkedAggregate bound rows = none ↔
      ¬(aggregate rows).within bound := by
  rw [checkedAggregate_spec]
  by_cases fits : (aggregate rows).within bound <;> simp [fits]

/-- Boundary projection of every row's net value. -/
def projectedNet : List Limbs → Int
  | [] => 0
  | row :: rows => row.net + projectedNet rows

/-- Projecting after aggregation agrees with adding the projected row nets. -/
theorem net_aggregate (rows : List Limbs) :
    (aggregate rows).net = projectedNet rows := by
  induction rows with
  | nil => simp [aggregate, projectedNet, Limbs.zero, Limbs.net]
  | cons row rows ih =>
      simp only [aggregate, projectedNet]
      rw [Limbs.net_merge, ih]

/-- Zero accounting support means every represented accounting row has zero
debit and zero credit. This is deliberately not a protocol-level state no-op
or an external admission rule. -/
def ZeroAccountingSupport (rows : List Limbs) : Prop :=
  ∀ row, row ∈ rows → row = Limbs.zero

theorem merge_eq_zero_iff (left right : Limbs) :
    left.merge right = Limbs.zero ↔
      left = Limbs.zero ∧ right = Limbs.zero := by
  cases left with
  | mk leftDebit leftCredit =>
    cases right with
    | mk rightDebit rightCredit =>
      simp only [Limbs.merge, Limbs.zero, Limbs.mk.injEq]
      omega

/-- Monotonicity makes aggregate-zero equivalent to row-wise zero accounting
support. Cancellation cannot satisfy this accounting-only predicate. -/
theorem zeroAccountingSupport_iff_aggregate_eq_zero (rows : List Limbs) :
    ZeroAccountingSupport rows ↔ aggregate rows = Limbs.zero := by
  induction rows with
  | nil => simp [ZeroAccountingSupport, aggregate]
  | cons row rows ih =>
      simp [ZeroAccountingSupport, aggregate, merge_eq_zero_iff, ← ih]

theorem cancelling_row_has_nonzero_accounting_support :
    projectedNet [Limbs.mk 1 1] = 0 ∧
      ¬ZeroAccountingSupport [Limbs.mk 1 1] := by
  constructor
  · decide
  · intro noOp
    have impossible := noOp (Limbs.mk 1 1) (by simp)
    exact (by decide : Limbs.mk 1 1 ≠ Limbs.zero) impossible

/-- The empty list is the internal fold identity. This theorem does not reject
an external segment whose authenticated journal has no accounting rows. -/
theorem checkedAggregate_empty_identity (bound : Nat) :
    checkedAggregate bound [] = some Limbs.zero := by
  rfl

/-- A segment can carry an authenticated nonempty journal independently of its
possibly empty accounting-row support. State transition semantics are kept
abstract because they are outside this accounting module. -/
structure AuthenticatedSegment (JournalEntry : Type) where
  journalHead : JournalEntry
  journalTail : List JournalEntry
  accountingRows : List Limbs

def AuthenticatedSegment.withEmptyAccounting {JournalEntry : Type}
    (journalHead : JournalEntry) (journalTail : List JournalEntry) :
    AuthenticatedSegment JournalEntry :=
  ⟨journalHead, journalTail, []⟩

/-- A nonempty authenticated journal may have empty accounting support; its
accounting fold still returns the internal identity. -/
theorem AuthenticatedSegment.emptyAccounting_fold_identity
    {JournalEntry : Type} (bound : Nat)
    (journalHead : JournalEntry) (journalTail : List JournalEntry) :
    checkedAggregate bound
      (AuthenticatedSegment.withEmptyAccounting
        journalHead journalTail).accountingRows = some Limbs.zero := by
  rfl

/-- A merge tree is nonempty by construction. It therefore needs no synthetic
identity leaf merely to encode tree shape. -/
inductive MergeTree where
  | leaf (row : Limbs)
  | node (left right : MergeTree)
deriving Repr, DecidableEq

def MergeTree.rows : MergeTree → List Limbs
  | .leaf row => [row]
  | .node left right => left.rows ++ right.rows

def MergeTree.total : MergeTree → Limbs
  | .leaf row => row
  | .node left right => left.total.merge right.total

def MergeTree.evaluate (bound : Nat) : MergeTree → Option Limbs
  | .leaf row => if row.within bound then some row else none
  | .node left right =>
      (left.evaluate bound).bind fun leftValue =>
        (right.evaluate bound).bind fun rightValue =>
          checkedMerge bound leftValue rightValue

theorem MergeTree.total_eq_aggregate_rows (tree : MergeTree) :
    tree.total = aggregate tree.rows := by
  induction tree with
  | leaf row => simp [MergeTree.total, MergeTree.rows, aggregate]
  | node left right leftIH rightIH =>
      simp only [MergeTree.total, MergeTree.rows]
      rw [aggregate_append, ← leftIH, ← rightIH]

/-- Every nonempty binary proof tree has the same complete specification as the
list fold. Tree shape cannot change success, failure, or the returned value. -/
theorem MergeTree.evaluate_spec (bound : Nat) (tree : MergeTree) :
    tree.evaluate bound =
      if tree.total.within bound then some tree.total else none := by
  induction tree with
  | leaf row => simp [MergeTree.evaluate, MergeTree.total]
  | node left right leftIH rightIH =>
      simp only [MergeTree.evaluate, MergeTree.total]
      rw [leftIH, rightIH]
      by_cases totalFits : (left.total.merge right.total).within bound
      · have leftFits : left.total.within bound :=
          within_left_of_merge totalFits
        have rightFits : right.total.within bound :=
          within_right_of_merge totalFits
        simp [leftFits, rightFits, checkedMerge, totalFits]
      · by_cases leftFits : left.total.within bound
        · by_cases rightFits : right.total.within bound
          · simp [leftFits, rightFits, checkedMerge, totalFits]
          · simp [leftFits, rightFits, totalFits]
        · simp [leftFits, totalFits]

theorem MergeTree.evaluate_eq_some_iff
    (bound : Nat) (tree : MergeTree) (result : Limbs) :
    tree.evaluate bound = some result ↔
      tree.total.within bound ∧ result = tree.total := by
  rw [tree.evaluate_spec]
  by_cases fits : tree.total.within bound <;> simp [fits, eq_comm]

theorem MergeTree.evaluate_eq_none_iff
    (bound : Nat) (tree : MergeTree) :
    tree.evaluate bound = none ↔ ¬tree.total.within bound := by
  rw [tree.evaluate_spec]
  by_cases fits : tree.total.within bound <;> simp [fits]

/-- Exact row coverage makes checked evaluation invariant under arbitrary
binary tree shape and accounting-row permutation. -/
theorem MergeTree.evaluate_eq_of_exact_coverage
    (bound : Nat) {left right : MergeTree}
    (coverage : CoversExactly left.rows right.rows) :
    left.evaluate bound = right.evaluate bound := by
  rw [left.evaluate_spec, right.evaluate_spec]
  have sameTotal : left.total = right.total := by
    rw [left.total_eq_aggregate_rows, right.total_eq_aggregate_rows]
    exact aggregate_eq_of_exact_coverage coverage
  rw [sameTotal]

/-- The checked list fold and any exactly covering tree agree. -/
theorem checkedAggregate_eq_tree_of_exact_coverage
    (bound : Nat) (rows : List Limbs) (tree : MergeTree)
    (coverage : CoversExactly rows tree.rows) :
    checkedAggregate bound rows = tree.evaluate bound := by
  rw [checkedAggregate_spec, tree.evaluate_spec,
    tree.total_eq_aggregate_rows]
  have sameTotal : aggregate rows = aggregate tree.rows :=
    aggregate_eq_of_exact_coverage coverage
  rw [sameTotal]

/-- When accounting support is nonempty, this wrapper commits its list order
and makes the absence of a synthetic identity leaf explicit. It is optional:
`AuthenticatedSegment` also permits genuinely empty accounting support. -/
structure CanonicalRows where
  head : Limbs
  tail : List Limbs
deriving Repr, DecidableEq

def CanonicalRows.toList (rows : CanonicalRows) : List Limbs :=
  rows.head :: rows.tail

def CanonicalRows.toTree : CanonicalRows → MergeTree
  | ⟨head, []⟩ => .leaf head
  | ⟨head, next :: rest⟩ =>
      .node (.leaf head) (CanonicalRows.toTree ⟨next, rest⟩)

@[simp] theorem CanonicalRows.toTree_rows (rows : CanonicalRows) :
    rows.toTree.rows = rows.toList := by
  cases rows with
  | mk head tail =>
      induction tail generalizing head with
      | nil => simp [CanonicalRows.toTree, CanonicalRows.toList,
          MergeTree.rows]
      | cons next rest ih =>
          simp [CanonicalRows.toTree, CanonicalRows.toList,
            MergeTree.rows, ih]

/-- The canonical right-associated tree is extensionally equal to the checked
fold of its committed nonempty row manifest. -/
theorem CanonicalRows.checkedAggregate_eq_toTree
    (bound : Nat) (rows : CanonicalRows) :
    checkedAggregate bound rows.toList = rows.toTree.evaluate bound := by
  apply checkedAggregate_eq_tree_of_exact_coverage
  simp [CoversExactly]

end ZrmAccountingAggregateV1.AccountingFoldTree
