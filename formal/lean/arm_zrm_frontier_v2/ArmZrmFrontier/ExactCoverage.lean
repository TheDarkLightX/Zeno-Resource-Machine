import Init.Data.List.Perm

namespace ArmZrmFrontier.ExactCoverage

/-- Exact coverage is multiset equality, not one-way membership. It therefore
tracks multiplicity and rejects missing and extra entries. -/
def CoversExactly {α : Type} (manifest observed : List α) : Prop :=
  List.Perm manifest observed

theorem length_eq {α : Type} {manifest observed : List α}
    (coverage : CoversExactly manifest observed) :
    manifest.length = observed.length :=
  coverage.length_eq

theorem mem_iff {α : Type} {manifest observed : List α}
    (coverage : CoversExactly manifest observed) (item : α) :
    item ∈ manifest ↔ item ∈ observed :=
  coverage.mem_iff

/-- Independently exact partitions compose without weakening exactness. -/
theorem append {α : Type}
    {leftManifest leftObserved rightManifest rightObserved : List α}
    (left : CoversExactly leftManifest leftObserved)
    (right : CoversExactly rightManifest rightObserved) :
    CoversExactly
      (leftManifest ++ rightManifest)
      (leftObserved ++ rightObserved) :=
  left.append right

example : CoversExactly [0, 1, 2] [2, 0, 1] := by
  exact
    ((List.Perm.swap 1 2 []).symm.cons 0).trans
      (List.Perm.swap 2 0 [1])

example : ¬ CoversExactly [0, 1, 2] [0, 1] := by
  intro coverage
  have lengths := coverage.length_eq
  simp at lengths

example : ¬ CoversExactly [0, 1, 2] [0, 1, 2, 2] := by
  intro coverage
  have lengths := coverage.length_eq
  simp at lengths

end ArmZrmFrontier.ExactCoverage
