import Init.Data.Fin.Lemmas

namespace ArmZrmFrontier.TotalCarrier

/-- A total modular carrier. `Fin n` makes every inhabitant a canonical residue;
there is no partial "nonzero representative" side condition. -/
abbrev Carrier (n : Nat) := Fin n

/-- Modular addition is total on the carrier, including at residue zero. -/
def add {n : Nat} (left right : Carrier n) : Carrier n := left + right

/-- The carrier operation is associative for every modulus. -/
theorem add_assoc {n : Nat} (a b c : Carrier n) :
    add (add a b) c = add a (add b c) := by
  apply Fin.ext
  change (((a.val + b.val) % n + c.val) % n) =
    ((a.val + (b.val + c.val) % n) % n)
  rw [Nat.mod_add_mod, Nat.add_mod_mod, Nat.add_assoc]

/-- Zero is a left identity whenever the modulus is inhabited. -/
theorem zero_add {n : Nat} [NeZero n] (a : Carrier n) :
    add 0 a = a := by
  apply Fin.ext
  simp [add]

/-- Zero is a right identity whenever the modulus is inhabited. -/
theorem add_zero {n : Nat} [NeZero n] (a : Carrier n) :
    add a 0 = a := by
  apply Fin.ext
  simp [add]

/-- Regression witness: the formerly awkward zero result remains in-domain. -/
example : add (1 : Carrier 7) (6 : Carrier 7) = 0 := by decide

end ArmZrmFrontier.TotalCarrier
