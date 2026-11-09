# Independent Mathematical Review Brief for Mehran

## 1. Purpose of this document

The empirical paper, optimizer, scenario generator, experiments, figures, tests, and four formal proofs are complete. Your task is to independently verify M1--M4, identify any hidden assumption or counterexample, and return corrections in proof-ready English and LaTeX. The manuscript must not claim more than the stated assumptions support.

Please do **not** assume that a statement is true merely because it appears in the manuscript. If a claim needs a stronger hypothesis or a different abstraction, state that clearly and provide corrected replacement text.

## 2. Files to read

Read these files in this order:

1. `manuscript/main.pdf` — Sections 3–5 (threat model, optimization, and formal analysis);
2. `manuscript/main.tex` — exact LaTeX notation and equation labels;
3. `src/minpause/model.py` — computational objects;
4. `src/minpause/optimizer.py` — exact subset-enumeration solver;
5. `tests/test_optimizer.py` — currently enforced behaviour.

You do not need to inspect the experiment CSV or plotting code unless a proof reveals a mismatch with the implementation.

## 3. Fixed problem definition

Let:

- $F$ be the finite set of independently pausable protocol operations;
- $R\subseteq F$ be the protected recovery set;
- $\mathcal P=\{P_1,\ldots,P_m\}$ be the supplied family of attack paths, where $P_k\subseteq F$;
- $x_f\in\{0,1\}$ indicate whether operation $f$ is paused;
- $c_f\ge0$ be the legitimate-use cost of pausing $f$;
- $c_{fg}\ge0$ be the pause cost borne by group $g$;
- $B_g(x)$ be group $g$'s normalized blocked-use burden; and
- $\Delta(x)=\max_g B_g(x)-\min_g B_g(x)$.

The implemented optimization problem is

$$
\min_{x\in\{0,1\}^{|F|}}
\left[
\sum_{f\in F}c_fx_f+\lambda\Delta(x)
\right]
$$

subject to

$$
\sum_{f\in P_k}x_f\ge1,
\qquad k=1,\ldots,m,
$$

and

$$
x_r=0,
\qquad r\in R.
$$

The reference implementation uses

$$
R=\{\textsf{repay},\textsf{addCollateral}\}.
$$

## 4. M1 — Attack-path coverage

### Proposed claim

If the paused set $X=\{f\in F:x_f=1\}$ satisfies

$$
X\cap P_k\neq\varnothing
\qquad\forall P_k\in\mathcal P,
$$

then no attack trace represented by $\mathcal P$ remains executable after pausing $X$.

### Main issue to resolve

The implementation stores each path as a **set of operation labels**, while a real execution trace is ordered and may invoke the same operation more than once. A proof must therefore state exactly when replacing a trace by its label support is sound.

### Suggested formalization

Use a labelled transition system

$$
\mathcal T=(S,F,\rightarrow),
$$

where $s\xrightarrow{f}s'$ is a state transition labelled by operation $f$. For a trace

$$
\pi=(s_0,f_1,s_1,\ldots,f_q,s_q),
$$

define its support by

$$
\operatorname{supp}(\pi)=\{f_1,\ldots,f_q\}.
$$

Pausing $X$ removes all transitions whose labels belong to $X$. A possible theorem is then conditional on every prohibited trace $\pi$ having an exact represented support $P_k=\operatorname{supp}(\pi)$. A more general formulation may let $P_k$ contain only operation labels that are mandatory in every trace it represents, so that $P_k\subseteq\operatorname{supp}(\pi)$, while also requiring every prohibited trace to be covered by at least one such $P_k$. A simple superset over-approximation is not sufficient: the selected paused operation could be an extra label absent from the real trace.

### Required output

- A precise theorem statement;
- definitions of “represented trace,” “paused transition system,” and the soundness assumption;
- a short proof, probably by contradiction;
- a paragraph explaining what the theorem does **not** guarantee when the supplied path family is incomplete.

## 5. M2 — Feasibility characterization

### Candidate condition

$$
\forall P_k\in\mathcal P,
\qquad P_k\setminus R\neq\varnothing.
$$

### Proposed claim

If every operation in $F\setminus R$ is independently pausable and there are no additional constraints, the MinPause feasibility problem has a solution if and only if every path contains at least one non-recovery operation.

### Candidate proof route

- **Necessity:** if some $P_k\subseteq R$, all variables in that path are fixed to zero, contradicting its coverage constraint.
- **Sufficiency:** if every $P_k\setminus R$ is nonempty, pausing every operation in $F\setminus R$ satisfies every path-coverage constraint.

### Boundary cases to address

- empty attack paths;
- an operation listed in a path but lacking a real pause flag;
- duplicated paths;
- $\mathcal P=\varnothing$;
- additional operational constraints not present in the current model.

### Required output

- A corrected iff proposition;
- a proof of both directions;
- an explicit list of assumptions under which the proposition holds.

## 6. M3 — Borrower recovery

Borrower $i$ has collateral $C_i$, debt $D_i$, liquidation threshold $\ell_i$, maximum available repayment $A_i^D$, and maximum additional collateral $A_i^C$. The pre-action health factor is

$$
H_i=\frac{\ell_iC_i}{D_i}.
$$

After repayment $a_D$ and collateral addition $a_C$,

$$
H_i'=\frac{\ell_i(C_i+a_C)}{D_i-a_D},
$$

with

$$
0\le a_D\le A_i^D,
\qquad
0\le a_C\le A_i^C.
$$

### Candidate resource condition

When $A_i^D<D_i$, recovery appears possible exactly when

$$
\ell_i(C_i+A_i^C)\ge D_i-A_i^D.
$$

If full repayment $A_i^D\ge D_i$ is permitted, the zero-debt boundary must be treated separately rather than dividing by zero.

### Items to establish

1. Monotonicity of $H_i'$ in $a_C$;
2. monotonicity of $H_i'$ in $a_D$ on $0\le a_D<D_i$;
3. necessary and sufficient resource conditions for reaching $H_i'\ge1$;
4. a finite-reachability statement under clearly specified transaction-size assumptions;
5. the distinction between an action being callable and a user having enough resources to recover.

### Required output

- One proposition for monotonicity;
- one proposition or corollary for exact recoverability;
- a careful treatment of full repayment and zero debt;
- proof text suitable for direct insertion into the paper.

Do not state that every borrower can recover. The experiment reports only the fraction satisfying the resource condition.

## 7. M4 — Computational complexity

### Proposed claim

With $R=\varnothing$, $\lambda=0$, and a decision threshold $K$, the decision version of MinPause is NP-complete and the optimization version is NP-hard.

### Suggested reduction

Reduce from weighted hitting set:

- weighted-hitting-set elements become pausable operations $f\in F$;
- each set to be hit becomes an attack path $P_k$;
- element weights become pause costs $c_f$;
- the hitting-set budget becomes the MinPause threshold $K$.

Show that a hitting set of total weight at most $K$ exists if and only if a pause policy with cost at most $K$ covers every attack path.

### Required output

- A formal decision-problem definition;
- membership in NP;
- the polynomial reduction and both directions of equivalence;
- a short explanation that the deployed exact solver is still practical because the reference system has only nine operations and seven non-recovery candidates.

Do not claim polynomial-time optimality for arbitrary $|F|$.

## 8. Required final deliverable

Please return:

1. corrected LaTeX statements for M1–M4;
2. confirmation or corrected versions of the four proofs;
3. one consolidated assumption list;
4. a list of any required changes to the Python model or tests;
5. a short note identifying which claims are exact theorems and which remain modelling assumptions.

The review should target Section 5. Empirical numbers and plots should remain unchanged unless a discovered mathematical inconsistency affects the implementation.

## 9. Completion checklist

- [ ] Trace abstraction defined and justified;
- [ ] path-coverage theorem proved or corrected;
- [ ] feasibility iff condition proved or corrected;
- [ ] exact recovery resource condition derived;
- [ ] full-repayment boundary handled;
- [ ] NP-completeness/NP-hardness proof independently verified;
- [ ] assumptions cross-checked against code;
- [ ] any replacement LaTeX returned without unresolved placeholders.

