namespace ArmZrmFrontier.TranscriptSeparation

/-- Order-sensitive accepted-journal material. This wrapper deliberately has no
coercion to `CanonicalSet`. -/
structure OrderedTrace (α : Type) where
  entries : List α
deriving Repr, DecidableEq

def OrderedTrace.append {α : Type}
    (left right : OrderedTrace α) : OrderedTrace α :=
  ⟨left.entries ++ right.entries⟩

/-- An order-insensitive semantic set, represented extensionally by its
characteristic function. This is a semantic model, not a serialization format. -/
structure CanonicalSet (α : Type) where
  contains : α → Bool

def CanonicalSet.union {α : Type}
    (left right : CanonicalSet α) : CanonicalSet α :=
  ⟨fun item => left.contains item || right.contains item⟩

@[ext] theorem CanonicalSet.ext {α : Type}
    {left right : CanonicalSet α}
    (same : ∀ item, left.contains item = right.contains item) : left = right := by
  cases left
  cases right
  simp_all only [mk.injEq]
  funext item
  exact same item

/-- Canonical-set union is commutative. Ordered-trace append is not. -/
theorem CanonicalSet.union_comm {α : Type}
    (left right : CanonicalSet α) :
    CanonicalSet.union left right = CanonicalSet.union right left := by
  ext item
  simp [CanonicalSet.union, Bool.or_comm]

inductive TraceToken where
  | first
  | second
deriving Repr, DecidableEq

def firstTrace : OrderedTrace TraceToken := ⟨[.first]⟩
def secondTrace : OrderedTrace TraceToken := ⟨[.second]⟩

/-- Concrete witness that journal order must not be normalized as a set. -/
theorem ordered_append_noncommutative :
    OrderedTrace.append firstTrace secondTrace ≠
      OrderedTrace.append secondTrace firstTrace := by
  decide

end ArmZrmFrontier.TranscriptSeparation
