import Lean.Elab.Tactic.Omega

namespace ArmZrmFrontier.AccountingStrongAssociativity

/-- Fixed-width signed net addition can make the *definedness* of a three-item
fold depend on parenthesization. This executable model checks a symmetric
inclusive bound. -/
def checkedSignedAdd (bound left right : Int) : Option Int :=
  let total := left + right
  if -bound ≤ total ∧ total ≤ bound then some total else none

def signedLeftFold3 (bound a b c : Int) : Option Int :=
  (checkedSignedAdd bound a b).bind fun ab => checkedSignedAdd bound ab c

def signedRightFold3 (bound a b c : Int) : Option Int :=
  (checkedSignedAdd bound b c).bind fun bc => checkedSignedAdd bound a bc

/-- At bound 127, cancellation makes the right grouping valid while the left
grouping overflows at its intermediate result. -/
theorem signed_definedness_counterexample :
    signedLeftFold3 127 127 1 (-1) = none ∧
    signedRightFold3 127 127 1 (-1) = some 127 := by
  decide

/-- A recursive accounting row stores monotone debit and credit totals rather
than a cancelling bounded net. Equal nonzero limbs are retained as coverage. -/
structure Limbs where
  debit : Nat
  credit : Nat
deriving Repr, DecidableEq

def Limbs.zero : Limbs := ⟨0, 0⟩

def Limbs.merge (left right : Limbs) : Limbs :=
  ⟨left.debit + right.debit, left.credit + right.credit⟩

def Limbs.within (bound : Nat) (value : Limbs) : Prop :=
  value.debit ≤ bound ∧ value.credit ≤ bound

instance (bound : Nat) (value : Limbs) : Decidable (value.within bound) :=
  inferInstanceAs (Decidable (value.debit ≤ bound ∧ value.credit ≤ bound))

def checkedMerge (bound : Nat) (left right : Limbs) : Option Limbs :=
  let total := left.merge right
  if total.within bound then some total else none

def limbLeftFold3 (bound : Nat) (a b c : Limbs) : Option Limbs :=
  (checkedMerge bound a b).bind fun ab => checkedMerge bound ab c

def limbRightFold3 (bound : Nat) (a b c : Limbs) : Option Limbs :=
  (checkedMerge bound b c).bind fun bc => checkedMerge bound a bc

theorem Limbs.merge_assoc (a b c : Limbs) :
    (a.merge b).merge c = a.merge (b.merge c) := by
  cases a
  cases b
  cases c
  simp [Limbs.merge, Nat.add_assoc]

/-- Monotonicity makes the partial bounded fold strongly associative: both
parenthesizations have the same value *and* the same definedness. -/
theorem checkedMerge_strong_assoc (bound : Nat) (a b c : Limbs) :
    limbLeftFold3 bound a b c = limbRightFold3 bound a b c := by
  cases a with
  | mk ad ac =>
    cases b with
    | mk bd bc =>
      cases c with
      | mk cd cc =>
        by_cases total :
            ad + bd + cd ≤ bound ∧ ac + bc + cc ≤ bound
        · have leftIntermediate :
              ad + bd ≤ bound ∧ ac + bc ≤ bound := by omega
          have rightIntermediate :
              bd + cd ≤ bound ∧ bc + cc ≤ bound := by omega
          have rightTotal :
              ad + (bd + cd) ≤ bound ∧ ac + (bc + cc) ≤ bound := by omega
          simp [
            limbLeftFold3, limbRightFold3, checkedMerge, Limbs.merge,
            Limbs.within, leftIntermediate, rightIntermediate,
            rightTotal, Nat.add_assoc
          ]
        · have rightTotal :
              ¬(ad + (bd + cd) ≤ bound ∧ ac + (bc + cc) ≤ bound) := by
            omega
          by_cases leftIntermediate :
              ad + bd ≤ bound ∧ ac + bc ≤ bound <;>
            by_cases rightIntermediate :
              bd + cd ≤ bound ∧ bc + cc ≤ bound <;>
            simp [
              limbLeftFold3, limbRightFold3, checkedMerge, Limbs.merge,
              Limbs.within, leftIntermediate, rightIntermediate,
              rightTotal, Nat.add_assoc
            ]

/-- If the complete monotone totals fit, both trees succeed with the exact
three-input result. -/
theorem checkedMerge_three_of_total_within
    (bound : Nat) (a b c : Limbs)
    (fits : ((a.merge b).merge c).within bound) :
    limbLeftFold3 bound a b c = some ((a.merge b).merge c) ∧
    limbRightFold3 bound a b c = some (a.merge (b.merge c)) := by
  cases a with
  | mk ad ac =>
    cases b with
    | mk bd bc =>
      cases c with
      | mk cd cc =>
        simp only [Limbs.merge, Limbs.within] at fits
        have leftIntermediate :
            ad + bd ≤ bound ∧ ac + bc ≤ bound := by omega
        have rightIntermediate :
            bd + cd ≤ bound ∧ bc + cc ≤ bound := by omega
        have rightTotal :
            ad + (bd + cd) ≤ bound ∧ ac + (bc + cc) ≤ bound := by omega
        simp [
          limbLeftFold3, limbRightFold3, checkedMerge, Limbs.merge,
          Limbs.within, leftIntermediate, rightIntermediate,
          rightTotal, Nat.add_assoc
        ]

/-- Cancellation is a projection at the boundary; it does not erase the
monotone coverage carried through recursion. -/
def Limbs.net (value : Limbs) : Int :=
  Int.ofNat value.credit - Int.ofNat value.debit

theorem Limbs.net_merge (left right : Limbs) :
    (left.merge right).net = left.net + right.net := by
  cases left
  cases right
  simp [Limbs.merge, Limbs.net]
  omega

example : (Limbs.mk 1 1).net = 0 := by decide
example : Limbs.mk 1 1 ≠ Limbs.zero := by decide

end ArmZrmFrontier.AccountingStrongAssociativity
