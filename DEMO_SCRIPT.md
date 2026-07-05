# Demo Script — Memory Immune System

Target length: ~3.5–4 minutes. Speak at a measured pace, pause 1–2s after each
action so the UI animation/graph settles before you talk over it.

Pre-recording checklist:
- [ ] Backend running (`uvicorn`) and healthy: `curl localhost:8000/health`
- [ ] Frontend running, all 6 sources show `CLEAN` in graph-state (fresh ingest)
- [ ] Screen recording area framed on the browser window, console/terminal hidden
- [ ] Have this script open on a second monitor or printed

---

## 1. Cold open — the problem (0:00–0:20)

*(Face-to-camera or voiceover over a blank/title screen, before touching the app)*

> "Every team building AI agents right now is quietly building up a memory
> problem. You feed an agent your Slack messages, your policy docs, your
> meeting notes — and eventually, some of that memory is wrong. Outdated.
> Contradicted. Sometimes even *maliciously* injected. Most agent memory
> systems have no idea. They'll retrieve the wrong document with the same
> confidence as the right one, and just... answer. Today I'm showing you a
> Memory Immune System — it detects that poisoning, quarantines it, repairs
> it, and can permanently forget it. All built on top of Cognee."

---

## 2. What we built, in one breath (0:20–0:40)

*(Switch to the app, full dashboard visible)*

> "This is a compliance knowledge base for a fictional company — Verdant
> Loop Analytics. It's ingested six real documents: two versions of a data
> retention policy, an unapproved 'rogue' draft that contradicts the
> official policy, two Slack threads, and a meeting transcript that
> resolves the conflict. Somewhere in there is bad information that's been
> mixed in with the good. My job — and my agent's job — is to find it,
> without me telling it in advance what's wrong."

---

## 3. Ingestion (0:40–0:55)

*(Click "Load Demo Corpus" if not already loaded — otherwise just gesture at the panel)*

> "Ingestion isn't a toy pipeline — every one of these documents goes
> through Cognee's real `remember()` call. That means chunking, entity
> extraction, and knowledge graph construction, not just 'store some text
> and embed it.' You can see each file move from Ingesting to Remembered to
> Mapped to Graph."

---

## 4. Ask — Before (0:55–1:25)

*(Type or point at the pre-filled query, click "Before", let the answer render)*

> "Let's ask the agent the question that matters: what's the current rule
> for EU customer data retention? I'll toggle to 'Before' — this is a
> frozen snapshot of what the agent believed the moment this memory got
> poisoned, before any immune response ran."
>
> *(read the answer aloud)*
>
> "It's confidently telling me EU customer records can be retained
> indefinitely. That's wrong — and worse, it sounds completely
> authoritative. This is the actual failure mode: not the agent refusing to
> answer, but the agent answering fluently and wrong."

---

## 5. Scan — detection (1:25–1:55)

*(Click "Run Scan", let results populate, point at the graph as edges appear)*

> "Now the immune system runs. Under the hood, this pulls every retrieved
> chunk back out of Cognee, and hands them to an LLM acting as a conflict
> judge — not a hardcoded rule, an actual reasoning pass over the evidence."
>
> *(point at conflicts list)*
>
> "It correctly identifies the meeting transcript as the authoritative
> source, and flags the old policy, the rogue draft, and the Slack message
> amplifying it — as directly contradicting the current, approved policy.
> Notice the graph: red pulsing nodes are the ones just flagged. Green
> stays green — the system doesn't punish the correct documents just
> because they're *involved* in a conflict."

---

## 6. Repair — quarantine (1:55–2:15)

*(Click Quarantine on the flagged sources)*

> "This is the human-in-the-loop moment — or it can be automated. I
> quarantine the three bad sources. That updates our own confidence-tracked
> status layer, and triggers Cognee's `improve()` call, which feeds that
> signal back into its memory-weighting."

---

## 7. Ask — After (2:15–2:35)

*(Toggle to "After", let the answer render)*

> "Same question, same agent — but now the answer-building step filters out
> anything quarantined before it ever reaches the language model. Three
> years, automatic purge within thirty days, citing only the current
> policy, the meeting minutes, and the correct Slack thread. No hedging, no
> contradiction — because the contradiction is no longer in the context the
> model sees."

---

## 8. Forget — the dramatic beat (2:35–2:55)

*(Click "Forget these memories", let the fade animation play)*

> "But filtering isn't enough for real compliance use cases — sometimes you
> need the data gone, not just ignored. This calls Cognee's `forget()`
> API with the specific document IDs — not a full wipe, a surgical
> deletion. I can prove it's real: if I query Cognee's raw memory right
> now, those three documents' chunks are just... gone. Not hidden. Deleted."

---

## 9. The callback — Before still works (2:55–3:10)

*(Toggle back to "Before" one more time)*

> "And this still works. Because we captured that frozen belief-state at
> ingestion time, I can show you exactly what the agent used to think —
> even though that bad memory has been permanently forgotten. That's the
> whole before-and-after story, provable, on demand."

---

## 10. Why Cognee (3:10–3:40)

> "This only works because Cognee gives us a real memory *lifecycle*, not
> just a vector store. `remember`, `recall`, `improve`, `forget` — four
> verbs that map directly onto how memory actually needs to behave in
> production: you add to it, you query it with graph-grounded reasoning —
> not just similarity search — you reinforce it based on feedback, and you
> can surgically delete from it at the document level."
---

## 11. Why it matters (3:40–4:00)

> "This isn't hypothetical. Every company with an AI agent sitting on top
> of Slack, Notion, policy PDFs, and old emails has this exact
> problem — stale docs, conflicting Slack takes, and yes, sometimes
> deliberately planted misinformation. Compliance and legal teams live in
> this world already. Giving an agent's memory an immune system — the
> ability to detect contradiction, quarantine it, repair from it, and
> prove what it forgot — is the difference between an agent you can put in
> front of a regulator, and one you can't."

---

## 12. Close (4:00–4:10)

> "Remember. Recall. Improve. Forget. That's not just Cognee's API — it's
> the lifecycle every trustworthy agent memory needs. Thanks for watching."

---

## Fallback / backup

If the live LLM call is slow or flaky during recording: the pre-recorded
fallback video (record one full successful run ahead of time) covers this.
Cut to it if any single step takes more than ~15 seconds to respond.

## 60-second version (if a strict time limit applies)

> "AI agents accumulate memory from Slack, docs, meetings — and some of it
> is wrong, outdated, or planted. This is a Memory Immune System built on
> Cognee. Watch: I ask about our EU data retention policy — before any
> repair, the agent confidently tells me records can be kept indefinitely.
> Wrong. I run a scan — an LLM conflict judge, not a hardcoded rule,
> compares every source and flags exactly the poisoned ones, while leaving
> the correct policy untouched. I quarantine them, ask again — now it's
> correct: three years, citing only verified sources. Then I permanently
> forget the bad memory using Cognee's real `forget()` API — I can prove
> it's gone from the underlying store, not just hidden. And the 'before'
> view still works afterward, because we froze that belief-state at
> ingestion. Remember, recall, improve, forget — that's the full lifecycle
> trustworthy agent memory needs, and Cognee is what makes it possible
> without us reinventing a graph database from scratch."
