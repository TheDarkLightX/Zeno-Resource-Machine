import Lean.Elab.Tactic.Omega

namespace ZrmAccountingAggregateV1.TotalOverflowCarrier

/-!
`Capped bound` totalizes bounded natural addition. Overflow is an explicit,
absorbing value rather than an undefined operation. This lets recursive
composition use a total commutative monoid while the boundary projection still
rejects overflow fail-closed.
-/

inductive Capped (bound : Nat) where
  | finite (value : Nat) (fits : value ≤ bound)
  | overflow
deriving Repr, DecidableEq

def Capped.zero (bound : Nat) : Capped bound :=
  .finite 0 (Nat.zero_le bound)

def Capped.ofNat (bound value : Nat) : Capped bound :=
  if fits : value ≤ bound then .finite value fits else .overflow

def Capped.merge {bound : Nat} : Capped bound → Capped bound → Capped bound
  | .overflow, _ => .overflow
  | _, .overflow => .overflow
  | .finite left _, .finite right _ =>
      if fits : left + right ≤ bound
      then .finite (left + right) fits
      else .overflow

/-- Overflow is absorbing on the left. -/
@[simp] theorem Capped.overflow_merge {bound : Nat} (value : Capped bound) :
    Capped.overflow.merge value = Capped.overflow := by
  cases value <;> rfl

/-- Overflow is absorbing on the right. -/
@[simp] theorem Capped.merge_overflow {bound : Nat} (value : Capped bound) :
    value.merge Capped.overflow = Capped.overflow := by
  cases value <;> rfl

@[simp] theorem Capped.zero_merge {bound : Nat} (value : Capped bound) :
    (Capped.zero bound).merge value = value := by
  cases value with
  | overflow => rfl
  | finite finiteValue finiteFits =>
      simp [Capped.zero, Capped.merge, finiteFits]

@[simp] theorem Capped.merge_zero {bound : Nat} (value : Capped bound) :
    value.merge (Capped.zero bound) = value := by
  cases value with
  | overflow => rfl
  | finite finiteValue finiteFits =>
      simp [Capped.zero, Capped.merge, finiteFits]

theorem Capped.merge_comm {bound : Nat} (left right : Capped bound) :
    left.merge right = right.merge left := by
  cases left with
  | overflow => simp
  | finite leftValue leftFits =>
      cases right with
      | overflow => simp
      | finite rightValue rightFits =>
          by_cases forwardFits : leftValue + rightValue ≤ bound
          · have reverseFits : rightValue + leftValue ≤ bound := by omega
            simp [Capped.merge, forwardFits, Nat.add_comm]
          · have reverseFails : ¬rightValue + leftValue ≤ bound := by omega
            simp [Capped.merge, forwardFits, reverseFails]

/-- Total strong associativity: every grouping yields the same finite value or
the same absorbing overflow sentinel. -/
theorem Capped.merge_assoc {bound : Nat}
    (first second third : Capped bound) :
    (first.merge second).merge third =
      first.merge (second.merge third) := by
  cases first with
  | overflow => simp
  | finite firstValue firstFits =>
      cases second with
      | overflow => simp
      | finite secondValue secondFits =>
          cases third with
          | overflow => simp
          | finite thirdValue thirdFits =>
              by_cases totalFits :
                  firstValue + secondValue + thirdValue ≤ bound
              · have firstPairFits :
                    firstValue + secondValue ≤ bound := by omega
                have secondPairFits :
                    secondValue + thirdValue ≤ bound := by omega
                have rightTotalFits :
                    firstValue + (secondValue + thirdValue) ≤ bound := by
                  omega
                simp [Capped.merge, firstPairFits, secondPairFits,
                  rightTotalFits, Nat.add_assoc]
              · have rightTotalFails :
                    ¬firstValue + (secondValue + thirdValue) ≤ bound := by
                  omega
                by_cases firstPairFits :
                    firstValue + secondValue ≤ bound <;>
                  by_cases secondPairFits :
                    secondValue + thirdValue ≤ bound <;>
                  simp [Capped.merge, firstPairFits, secondPairFits,
                    rightTotalFails, Nat.add_assoc]

/-- Fail-closed projection at an admission boundary. -/
def Capped.accept {bound : Nat} : Capped bound → Option Nat
  | .finite value _ => some value
  | .overflow => none

def Capped.IsFinite {bound : Nat} : Capped bound → Prop
  | .finite _ _ => True
  | .overflow => False

instance {bound : Nat} (value : Capped bound) :
    Decidable value.IsFinite := by
  cases value with
  | finite finiteValue finiteFits =>
      exact isTrue trivial
  | overflow =>
      exact isFalse (fun impossible => impossible)

@[simp] theorem Capped.accept_ofNat (bound value : Nat) :
    (Capped.ofNat bound value).accept =
      if value ≤ bound then some value else none := by
  by_cases fits : value ≤ bound <;>
    simp [Capped.ofNat, Capped.accept, fits]

/-- Capping commutes with exact natural addition. -/
theorem Capped.merge_ofNat (bound left right : Nat) :
    (Capped.ofNat bound left).merge (Capped.ofNat bound right) =
      Capped.ofNat bound (left + right) := by
  by_cases totalFits : left + right ≤ bound
  · have leftFits : left ≤ bound := by omega
    have rightFits : right ≤ bound := by omega
    simp [Capped.ofNat, Capped.merge, leftFits, rightFits, totalFits]
  · by_cases leftFits : left ≤ bound
    · by_cases rightFits : right ≤ bound
      · simp [Capped.ofNat, Capped.merge, leftFits, rightFits, totalFits]
      · simp [Capped.ofNat, leftFits, rightFits, totalFits]
    · simp [Capped.ofNat, leftFits, totalFits]

def exactSum : List Nat → Nat
  | [] => 0
  | value :: values => value + exactSum values

/-- Arbitrary recursive aggregation in the total carrier. -/
def aggregate (bound : Nat) : List Nat → Capped bound
  | [] => Capped.zero bound
  | value :: values =>
      (Capped.ofNat bound value).merge (aggregate bound values)

theorem aggregate_eq_ofNat_exactSum (bound : Nat) (values : List Nat) :
    aggregate bound values = Capped.ofNat bound (exactSum values) := by
  induction values with
  | nil => simp [aggregate, exactSum, Capped.zero, Capped.ofNat]
  | cons value values ih =>
      simp only [aggregate, exactSum, ih]
      exact Capped.merge_ofNat bound value (exactSum values)

/-- Direct finite/overflow characterization against the exact natural sum. -/
theorem aggregate_isFinite_iff (bound : Nat) (values : List Nat) :
    (aggregate bound values).IsFinite ↔ exactSum values ≤ bound := by
  rw [aggregate_eq_ofNat_exactSum]
  by_cases fits : exactSum values ≤ bound <;>
    simp [Capped.ofNat, Capped.IsFinite, fits]

/-- The final result is finite exactly when the unbounded mathematical sum is
within the bound; otherwise boundary projection returns `none`. -/
theorem accept_aggregate (bound : Nat) (values : List Nat) :
    (aggregate bound values).accept =
      if exactSum values ≤ bound then some (exactSum values) else none := by
  rw [aggregate_eq_ofNat_exactSum, Capped.accept_ofNat]

theorem accept_aggregate_eq_some_iff
    (bound : Nat) (values : List Nat) (result : Nat) :
    (aggregate bound values).accept = some result ↔
      exactSum values ≤ bound ∧ result = exactSum values := by
  rw [accept_aggregate]
  by_cases fits : exactSum values ≤ bound <;> simp [fits, eq_comm]

theorem accept_aggregate_eq_none_iff (bound : Nat) (values : List Nat) :
    (aggregate bound values).accept = none ↔
      ¬exactSum values ≤ bound := by
  rw [accept_aggregate]
  by_cases fits : exactSum values ≤ bound <;> simp [fits]

/-- A pointwise two-limb carrier inherits the total algebra. -/
structure CappedLimbs (bound : Nat) where
  debit : Capped bound
  credit : Capped bound
deriving Repr, DecidableEq

def CappedLimbs.zero (bound : Nat) : CappedLimbs bound :=
  ⟨Capped.zero bound, Capped.zero bound⟩

def CappedLimbs.merge {bound : Nat}
    (left right : CappedLimbs bound) : CappedLimbs bound :=
  ⟨left.debit.merge right.debit, left.credit.merge right.credit⟩

@[simp] theorem CappedLimbs.zero_merge {bound : Nat}
    (value : CappedLimbs bound) :
    (CappedLimbs.zero bound).merge value = value := by
  cases value
  simp [CappedLimbs.zero, CappedLimbs.merge]

@[simp] theorem CappedLimbs.merge_zero {bound : Nat}
    (value : CappedLimbs bound) :
    value.merge (CappedLimbs.zero bound) = value := by
  cases value
  simp [CappedLimbs.zero, CappedLimbs.merge]

theorem CappedLimbs.merge_comm {bound : Nat}
    (left right : CappedLimbs bound) :
    left.merge right = right.merge left := by
  cases left
  cases right
  simp [CappedLimbs.merge, Capped.merge_comm]

theorem CappedLimbs.merge_assoc {bound : Nat}
    (first second third : CappedLimbs bound) :
    (first.merge second).merge third =
      first.merge (second.merge third) := by
  cases first
  cases second
  cases third
  simp [CappedLimbs.merge, Capped.merge_assoc]

end ZrmAccountingAggregateV1.TotalOverflowCarrier
