#!/usr/bin/env tsx
/**
 * Paper Explain DAG Runner for Cursor
 *
 * Runs the paper explain pipeline by executing tasks in topological order.
 * Tasks in the same rank (no mutual dependencies) can run concurrently.
 *
 * Usage:
 *   tsx .cursor/run_paper_explain.ts "https://arxiv.org/abs/2602.05400"
 *   tsx .cursor/run_paper_explain.ts "https://arxiv.org/abs/2602.05400" --output-dir ./my_paper
 *
 * Requires:
 *   - @cursor/sdk (Cursor SDK)
 *   - tsx (TypeScript executor)
 */

import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DAG_PATH = resolve(__dirname, "paper_explain_dag.json");

interface Task {
  id: string;
  depends_on: string[];
  skill: string;
  subtask_prompt: string;
}

interface DagConfig {
  title: string;
  description: string;
  tasks: Task[];
}

type TaskStatus = "pending" | "running" | "completed" | "failed" | "skipped";

interface TaskState {
  id: string;
  status: TaskStatus;
  result?: string;
  error?: string;
}

function loadDag(path: string): DagConfig {
  const raw = readFileSync(path, "utf-8");
  return JSON.parse(raw) as DagConfig;
}

function topologicalSort(tasks: Task[]): Task[][] {
  const taskMap = new Map(tasks.map((t) => [t.id, t]));
  const ranks: Task[][] = [];
  const completed = new Set<string>();
  const failed = new Set<string>();

  while (completed.size + failed.size < tasks.length) {
    const rank: Task[] = [];
    for (const task of tasks) {
      if (completed.has(task.id) || failed.has(task.id)) continue;
      const depsReady = task.depends_on.every(
        (dep) => completed.has(dep) || !taskMap.has(dep)
      );
      const depsFailed = task.depends_on.some((dep) => failed.has(dep));
      if (depsReady && !depsFailed) {
        rank.push(task);
      } else if (depsFailed) {
        failed.add(task.id);
      }
    }
    if (rank.length === 0) break;
    for (const task of rank) {
      completed.add(task.id);
    }
    ranks.push(rank);
  }

  return ranks;
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: tsx .cursor/run_paper_explain.ts <archive_url> [--output-dir <dir>]");
    process.exit(1);
  }

  const archiveUrl = args[0];
  const dag = loadDag(DAG_PATH);

  console.log(`\nPaper Explain Pipeline`);
  console.log(`  Title: ${dag.title}`);
  console.log(`  Archive URL: ${archiveUrl}`);
  console.log(`  Tasks: ${dag.tasks.length}`);
  console.log();

  const ranks = topologicalSort(dag.tasks);
  const states = new Map<string, TaskState>();

  dag.tasks.forEach((t) => {
    states.set(t.id, { id: t.id, status: "pending" });
  });

  for (const [rankIndex, rank] of ranks.entries()) {
    console.log(`--- Rank ${rankIndex + 1} (${rank.length} task(s)) ---`);

    for (const task of rank) {
      const state = states.get(task.id)!;
      state.status = "running";
      console.log(`  [${task.id}] Starting (skill: ${task.skill})`);

      const enhancedPrompt = `${task.subtask_prompt}\n\n---\nInput: archive_url=${archiveUrl}`;

      console.log(`  [${task.id}] Prompt length: ${enhancedPrompt.length} chars`);

      // TODO: Replace this placeholder with actual Cursor SDK agent invocation:
      //   const agent = await Agent.create({
      //     local: { cwd: process.cwd() },
      //   });
      //   const run = await agent.send(enhancedPrompt);
      //   taskState.result = run.text;
      //   taskState.status = "completed";

      // Placeholder for demonstration:
      console.log(`  [${task.id}] (Stand-in: would invoke Cursor SDK agent here)`);
      state.status = "completed";
      state.result = `Placeholder result for ${task.id}`;
      console.log(`  [${task.id}] Completed`);
    }

    console.log();
  }

  // Summary
  console.log("=== Pipeline Summary ===");
  for (const [id, state] of states) {
    const status = state.status === "completed" ? "OK" : state.status === "skipped" ? "SKIP" : "FAIL";
    console.log(`  ${id}: ${status}`);
  }

  console.log("\nDone. To serve the generated website:");
  console.log("  cd <paper_dir>/website && python3 -m http.server 8000");
}

main().catch((err) => {
  console.error("Pipeline failed:", err);
  process.exit(1);
});
