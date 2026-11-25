//! Write cross-check vectors for the Python port of Zeno-ADP 0.8.0's
//! `state_discovery::RawModel::quotient` in `reference_models/bounded_explorer.py`.
//!
//! Without arguments: seeded random tables, with their inputs. With `--stdin`:
//! one table per input line, `symbols states start` then `states * symbols`
//! successors and `states * symbols` outcome codes; inputs are not echoed.
//! Output is JSON on stdout. The scorer of a word is the sum of the codes along
//! its path, so each score change is exactly one code.

use std::io::Read;

use zeno_adp::state_discovery::{Observer, Quotient, RawModel};

struct Lcg(u64);

impl Lcg {
    fn next(&mut self) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        self.0 >> 33
    }

    fn below(&mut self, n: u64) -> usize {
        usize::try_from(self.next() % n).expect("small")
    }
}

fn ints<T: std::fmt::Display>(values: &[T]) -> String {
    let items: Vec<String> = values.iter().map(ToString::to_string).collect();
    format!("[{}]", items.join(","))
}

fn table<T: std::fmt::Display>(rows: &[Vec<T>]) -> String {
    let items: Vec<String> = rows.iter().map(|row| ints(row)).collect();
    format!("[{}]", items.join(","))
}

fn solve(symbols: usize, start: usize, next: &[Vec<usize>], gains: &[Vec<i64>]) -> Quotient {
    let observer = Observer::new(symbols, start, next.to_vec()).expect("valid observer");
    let mut scorer = |word: &[usize]| -> i64 {
        let (mut state, mut total) = (start, 0i64);
        for &symbol in word {
            total += gains[state][symbol];
            state = next[state][symbol];
        }
        total
    };
    let raw = RawModel::read(observer, &mut scorer).expect("read");
    raw.quotient().expect("quotient").into_inner()
}

fn answer(q: &Quotient) -> String {
    let class_of: Vec<String> = q
        .class_of
        .iter()
        .map(|c| c.map_or_else(|| "null".to_string(), |c| c.to_string()))
        .collect();
    format!(
        "{{\"classes\":{},\"class_of\":[{}],\"start\":{},\"gains\":{},\"next\":{},\"probes\":{}}}",
        q.gains.len(),
        class_of.join(","),
        q.start,
        table(&q.gains),
        table(&q.next),
        table(&q.probes),
    )
}

fn random_case(rng: &mut Lcg, case: usize) -> String {
    let states = 1 + rng.below(if case < 60 { 8 } else { 24 } as u64);
    let symbols = 1 + rng.below(4);
    let codes = 1 + rng.below(4) as u64;
    let start = rng.below(states as u64);
    let next: Vec<Vec<usize>> = (0..states)
        .map(|_| (0..symbols).map(|_| rng.below(states as u64)).collect())
        .collect();
    let gains: Vec<Vec<i64>> = (0..states)
        .map(|_| {
            (0..symbols)
                .map(|_| i64::try_from(rng.below(codes)).expect("small"))
                .collect()
        })
        .collect();
    let q = solve(symbols, start, &next, &gains);
    format!(
        "{{\"case\":{case},\"symbols\":{symbols},\"start\":{start},\"next\":{},\"gains\":{},\"quotient\":{}}}",
        table(&next),
        table(&gains),
        answer(&q),
    )
}

fn stdin_cases() -> String {
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).expect("stdin");
    let mut out = Vec::new();
    for line in input.lines().filter(|line| !line.trim().is_empty()) {
        let values: Vec<i64> = line
            .split_whitespace()
            .map(|v| v.parse().expect("integer"))
            .collect();
        let as_index = |v: i64| usize::try_from(v).expect("index");
        let (symbols, states, start) = (as_index(values[0]), as_index(values[1]), as_index(values[2]));
        let cells = states * symbols;
        assert_eq!(values.len(), 3 + 2 * cells, "line length");
        let next: Vec<Vec<usize>> = values[3..3 + cells]
            .chunks(symbols)
            .map(|row| row.iter().map(|&v| as_index(v)).collect())
            .collect();
        let gains: Vec<Vec<i64>> = values[3 + cells..].chunks(symbols).map(<[i64]>::to_vec).collect();
        out.push(answer(&solve(symbols, start, &next, &gains)));
    }
    format!("[{}]", out.join(","))
}

fn main() {
    if std::env::args().nth(1).as_deref() == Some("--stdin") {
        println!("{}", stdin_cases());
        return;
    }
    let mut rng = Lcg(0x5a52_4d00_0800);
    let cases: Vec<String> = (0..120).map(|case| random_case(&mut rng, case)).collect();
    println!(
        "{{\"schema\":\"zrm/zeno-adp-quotient-vectors/v1\",\"zeno_adp\":\"0.8.0\",\"random\":[{}]}}",
        cases.join(",")
    );
}
