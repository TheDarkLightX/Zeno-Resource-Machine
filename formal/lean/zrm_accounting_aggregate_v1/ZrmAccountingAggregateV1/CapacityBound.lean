import ZrmAccountingAggregateV1.TotalOverflowCarrier

namespace ZrmAccountingAggregateV1.CapacityBound

open TotalOverflowCarrier

/-!
The candidate schema gives a `u32` leaf count and a `u128` value bound for
each leaf column. These theorems keep the exact natural-number calculation
separate from machine arithmetic and show that every valid column aggregate is
strictly below `2^160`, hence fits an exact `U256` limb.
-/

def u32Max : Nat := 2 ^ 32 - 1
def u128Max : Nat := 2 ^ 128 - 1
def u256Max : Nat := 2 ^ 256 - 1

theorem u32Max_mul_u128Max_lt_u160 :
    u32Max * u128Max < 2 ^ 160 := by
  decide

theorem u160_lt_u256 : 2 ^ 160 < 2 ^ 256 := by
  decide

theorem count_mul_leaf_lt_u160
    {leafCount leafValue : Nat}
    (countBound : leafCount ≤ u32Max)
    (valueBound : leafValue ≤ u128Max) :
    leafCount * leafValue < 2 ^ 160 := by
  have productBound :
      leafCount * leafValue ≤ u32Max * u128Max :=
    Nat.mul_le_mul countBound valueBound
  exact Nat.lt_of_le_of_lt productBound u32Max_mul_u128Max_lt_u160

theorem count_mul_leaf_lt_u256
    {leafCount leafValue : Nat}
    (countBound : leafCount ≤ u32Max)
    (valueBound : leafValue ≤ u128Max) :
    leafCount * leafValue < 2 ^ 256 :=
  Nat.lt_trans
    (count_mul_leaf_lt_u160 countBound valueBound)
    u160_lt_u256

/-- A list of individually bounded column values is bounded by its length
times the per-leaf maximum. -/
theorem exactSum_le_length_mul
    (values : List Nat) (leafMaximum : Nat)
    (eachBounded : ∀ value, value ∈ values → value ≤ leafMaximum) :
    exactSum values ≤ values.length * leafMaximum := by
  induction values with
  | nil => simp [exactSum]
  | cons value values ih =>
      have valueBound : value ≤ leafMaximum :=
        eachBounded value (by simp)
      have tailBounded :
          ∀ tailValue, tailValue ∈ values → tailValue ≤ leafMaximum := by
        intro tailValue tailMembership
        exact eachBounded tailValue (by simp [tailMembership])
      have tailSumBound := ih tailBounded
      simp only [exactSum, List.length_cons, Nat.succ_mul]
      omega

/-- Any valid segment column has an exact mathematical aggregate below
`2^160`. This theorem applies independently to consumed, created, burned, and
minted columns. -/
theorem valid_column_sum_lt_u160
    (values : List Nat)
    (countBound : values.length ≤ u32Max)
    (eachBounded : ∀ value, value ∈ values → value ≤ u128Max) :
    exactSum values < 2 ^ 160 := by
  have sumBound : exactSum values ≤ values.length * u128Max :=
    exactSum_le_length_mul values u128Max eachBounded
  have productBound :
      values.length * u128Max ≤ u32Max * u128Max :=
    Nat.mul_le_mul countBound (Nat.le_refl u128Max)
  exact Nat.lt_of_le_of_lt
    (Nat.le_trans sumBound productBound)
    u32Max_mul_u128Max_lt_u160

theorem valid_column_sum_lt_u256
    (values : List Nat)
    (countBound : values.length ≤ u32Max)
    (eachBounded : ∀ value, value ∈ values → value ≤ u128Max) :
    exactSum values < 2 ^ 256 :=
  Nat.lt_trans
    (valid_column_sum_lt_u160 values countBound eachBounded)
    u160_lt_u256

theorem valid_column_sum_le_u256Max
    (values : List Nat)
    (countBound : values.length ≤ u32Max)
    (eachBounded : ∀ value, value ∈ values → value ≤ u128Max) :
    exactSum values ≤ u256Max := by
  have belowU256 :=
    valid_column_sum_lt_u256 values countBound eachBounded
  simp only [u256Max]
  omega

/-- Under the schema bounds, the total overflow carrier at the U256 boundary
always projects to the exact natural sum; the overflow branch is unreachable
for a valid segment column. -/
theorem valid_column_u256_accepts_exact_sum
    (values : List Nat)
    (countBound : values.length ≤ u32Max)
    (eachBounded : ∀ value, value ∈ values → value ≤ u128Max) :
    (TotalOverflowCarrier.aggregate u256Max values).accept =
      some (exactSum values) := by
  rw [TotalOverflowCarrier.accept_aggregate]
  have fits :=
    valid_column_sum_le_u256Max values countBound eachBounded
  simp [fits]

end ZrmAccountingAggregateV1.CapacityBound
