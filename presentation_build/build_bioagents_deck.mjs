import fs from "node:fs/promises";
import path from "node:path";

const {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  layers,
  panel,
  text,
  shape,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  grow,
  fr,
  auto,
} = await import("file:///C:/Users/aacer/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs");

const OUT = "presentation_build/output";
const PREVIEWS = "presentation_build/previews";
const PPTX = `${OUT}/BioAgents_Presentation.pptx`;

await fs.mkdir(OUT, { recursive: true });
await fs.mkdir(PREVIEWS, { recursive: true });
for (const file of await fs.readdir(PREVIEWS)) {
  if (file.endsWith(".png") || file.endsWith(".layout.json")) {
    await fs.unlink(path.join(PREVIEWS, file));
  }
}

const W = 1920;
const H = 1080;

const colors = {
  ink: "#0D1B1E",
  slate: "#264044",
  muted: "#5D7376",
  paper: "#F6F8F4",
  mist: "#E5ECE6",
  mint: "#7BC7A5",
  teal: "#168E8A",
  blue: "#3275D8",
  amber: "#E4A83A",
  coral: "#CF5B4D",
  violet: "#6D5BD0",
  dark: "#071514",
  white: "#FFFFFF",
};

const font = "Aptos";
const display = "Aptos Display";

function t(value, opts = {}) {
  return text(value, {
    width: opts.width ?? fill,
    height: opts.height ?? hug,
    name: opts.name,
    columnSpan: opts.columnSpan,
    rowSpan: opts.rowSpan,
    style: {
      fontFace: opts.fontFace ?? font,
      fontSize: opts.size ?? 28,
      bold: opts.bold ?? false,
      color: opts.color ?? colors.ink,
      lineSpacingMultiple: opts.lineSpacingMultiple ?? 1.08,
      ...opts.style,
    },
  });
}

function titleSlide(presentation, title, subtitle, eyebrow, children, notes) {
  const slide = presentation.slides.add();
  slide.compose(
    layers(
      { name: "cover-layers", width: fill, height: fill },
      [
        shape({ name: "bg", width: fill, height: fill, fill: colors.dark }),
        grid(
          {
            name: "cover-root",
            width: fill,
            height: fill,
            columns: [fr(1.15), fr(0.85)],
            columnGap: 80,
            padding: { x: 112, y: 92 },
          },
          [
            column(
              { name: "cover-copy", width: fill, height: fill, gap: 34, justify: "center" },
              [
                t(eyebrow, { name: "cover-eyebrow", size: 24, bold: true, color: colors.mint, width: wrap(720) }),
                t(title, {
                  name: "cover-title",
                  size: 88,
                  bold: true,
                  color: colors.white,
                  fontFace: display,
                  width: fill,
                  lineSpacingMultiple: 0.94,
                }),
                rule({ name: "cover-rule", width: fixed(220), stroke: colors.mint, weight: 7 }),
                t(subtitle, { name: "cover-subtitle", size: 33, color: "#C8D9D5", width: wrap(820), lineSpacingMultiple: 1.12 }),
              ],
            ),
            children,
          ],
        ),
      ],
    ),
    { frame: { left: 0, top: 0, width: W, height: H }, baseUnit: 8 },
  );
  slide.speakerNotes.setText(notes);
  return slide;
}

function contentSlide(presentation, { eyebrow, title, subtitle, body, notes, dark = false }) {
  const slide = presentation.slides.add();
  slide.compose(
    column(
      {
        name: "slide-root",
        width: fill,
        height: fill,
        padding: { x: 92, y: 70 },
        gap: 34,
      },
      [
        column(
          { name: "title-stack", width: fill, height: hug, gap: 14 },
          [
            t(eyebrow, { name: "eyebrow", size: 18, bold: true, color: dark ? colors.mint : colors.teal, width: wrap(900) }),
            t(title, {
              name: "slide-title",
              size: 58,
              bold: true,
              color: dark ? colors.white : colors.ink,
              fontFace: display,
              width: wrap(1440),
              lineSpacingMultiple: 1.0,
            }),
            subtitle ? t(subtitle, { name: "subtitle", size: 25, color: dark ? "#B8CBC8" : colors.muted, width: wrap(1320) }) : shape({ width: fixed(1), height: fixed(1), fill: "transparent" }),
          ],
        ),
        body,
      ],
    ),
    { frame: { left: 0, top: 0, width: W, height: H }, baseUnit: 8 },
  );
  slide.background.fill = dark ? colors.dark : colors.paper;
  slide.speakerNotes.setText(notes);
  return slide;
}

function chip(label, color = colors.teal, opts = {}) {
  return panel(
    {
      name: opts.name,
      width: opts.width ?? fixed(170),
      height: hug,
      padding: { x: 18, y: 10 },
      borderRadius: "rounded-full",
      fill: opts.fill ?? color,
      align: "center",
    },
    t(label, { name: `${opts.name ?? "chip"}-text`, size: opts.size ?? 18, bold: true, color: opts.textColor ?? colors.white, width: fill }),
  );
}

function openBullet(head, detail, color = colors.teal) {
  return row(
    { name: `bullet-${head}`, width: fill, height: hug, gap: 18, align: "start" },
    [
      shape({ name: `dot-${head}`, width: fixed(14), height: fixed(14), borderRadius: "rounded-full", fill: color }),
      column(
        { name: `bullet-copy-${head}`, width: fill, height: hug, gap: 6 },
        [
          t(head, { name: `bullet-head-${head}`, size: 30, bold: true, color: colors.ink }),
          t(detail, { name: `bullet-detail-${head}`, size: 22, color: colors.muted, width: fill }),
        ],
      ),
    ],
  );
}

function stage(label, sub, color, height = 136, subSize = 19) {
  return panel(
    {
      name: `stage-${label}`,
      width: fill,
      height: fixed(height),
      padding: { x: 24, y: 14 },
      borderRadius: 18,
      fill: colors.white,
      line: { color: "#D5DFD8", width: 1 },
    },
    column(
      { width: fill, height: fill, gap: 8, justify: "center" },
      [
        chip(label, color, { name: `stage-chip-${label}` }),
        t(sub, { name: `stage-sub-${label}`, size: subSize, bold: true, color: colors.slate, width: fill }),
      ],
    ),
  );
}

function serviceNode(label, sub, color) {
  return panel(
    {
      name: `node-${label}`,
      width: fill,
      height: fixed(118),
      padding: { x: 22, y: 18 },
      borderRadius: 16,
      fill: colors.white,
      line: { color, width: 3 },
    },
    column(
      { width: fill, height: fill, gap: 6 },
      [
        t(label, { name: `node-title-${label}`, size: 23, bold: true, color: colors.ink, width: fill }),
        t(sub, { name: `node-sub-${label}`, size: 17, color: colors.muted, width: fill }),
      ],
    ),
  );
}

function makeDeck() {
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });

  titleSlide(
    presentation,
    "BioAgents",
    "A multi-agent AI layer for synthetic biology, catalyst screening, and explainable discovery workflows.",
    "OPENAI-PRIMARY. LOCAL FALLBACK. AGENT-READY.",
    panel(
      {
        name: "cover-orbit",
        width: fill,
        height: fill,
        padding: 24,
        borderRadius: 36,
        fill: "#0E2422",
        line: { color: "#31524B", width: 2 },
      },
      grid(
        { name: "cover-grid", width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], rows: [fr(1), fr(1), fr(1)], columnGap: 18, rowGap: 18 },
        [
          serviceNode("Compound", "Profiles and properties", colors.mint),
          serviceNode("Reaction", "Risk and interaction logic", colors.coral),
          serviceNode("Research", "Candidate discovery", colors.blue),
          serviceNode("Analysis", "Ranking and statistics", colors.amber),
          panel(
            { name: "core-node", width: fill, height: fill, padding: { x: 22, y: 20 }, borderRadius: 20, fill: colors.mint },
            column({ width: fill, height: fill, justify: "center", gap: 8 }, [
              t("Knowledge core", { name: "core-node-title", size: 27, bold: true, color: colors.dark, width: fill }),
              t("MeTTa facts + services", { name: "core-node-sub", size: 18, color: colors.dark, width: fill }),
            ]),
          ),
          serviceNode("Database", "PubChem lookup", colors.violet),
          serviceNode("LLM", "OpenAI insights", colors.teal),
          serviceNode("Feedback", "Experiment logs", colors.amber),
          serviceNode("uAgents", "Optional distributed runtime", colors.mint),
        ],
      ),
    ),
    "Introduce BioAgents as the bridge between structured scientific knowledge, practical web tooling, and optional autonomous-agent execution. Emphasize that the default app works without distributed infrastructure, while still supporting it.",
  );

  contentSlide(presentation, {
    eyebrow: "01 / PROBLEM",
    title: "Discovery workflows break when reasoning, data, and execution live in separate tools.",
    subtitle: "The pain is not just model quality. It is orchestration, traceability, and fallbacks.",
    body: grid(
      { name: "problem-grid", width: fill, height: fill, columns: [fr(1), fr(1.08)], columnGap: 64 },
      [
        column({ name: "problem-list", width: fill, height: fill, gap: 34, justify: "center" }, [
          openBullet("Fragmented context", "Compound properties, literature hints, external databases, and experiment notes are usually stitched manually.", colors.coral),
          openBullet("Brittle automation", "A demo that requires hidden local files, a live agent mesh, or a perfect API key is not operational software.", colors.amber),
          openBullet("Weak explainability", "Scientists need to see why a candidate was ranked, not just receive a generated answer.", colors.teal),
        ]),
        panel(
          { name: "problem-proof", width: fill, height: fixed(540), padding: 40, borderRadius: 30, fill: colors.white, line: { color: "#D4DED6", width: 1 } },
          column({ width: fill, height: fill, gap: 22, justify: "center" }, [
            t("Failure pattern", { name: "failure-label", size: 22, bold: true, color: colors.coral, width: fill }),
            t("Imports succeed on the author's machine, then a fresh clone cannot find core services.", { name: "failure-main", size: 48, bold: true, color: colors.ink, width: fill, lineSpacingMultiple: 1.02 }),
            rule({ width: fixed(360), stroke: colors.coral, weight: 5 }),
            t("BioAgents has to be packaged as a coherent product, not a pile of promising modules.", { name: "failure-caption", size: 25, color: colors.muted, width: fill }),
          ]),
        ),
      ],
    ),
    notes: "Frame the problem from the user's lived issue: a GitHub clone missing the service layer is exactly the kind of reliability failure the system must avoid. This slide sets up why architecture and tests matter, not just AI output.",
  });

  contentSlide(presentation, {
    eyebrow: "02 / SOLUTION",
    title: "BioAgents turns the repo into a working discovery layer with a stable service core.",
    subtitle: "Flask routes call committed services directly; OpenAI enhances the answer when available; local logic keeps the app useful otherwise.",
    body: grid(
      { name: "solution-grid", width: fill, height: fill, columns: [fr(1.2), fr(0.8)], columnGap: 70 },
      [
        column({ width: fill, height: fill, gap: 26, justify: "center" }, [
          t("The operating principle", { name: "solution-kicker", size: 24, bold: true, color: colors.teal, width: fill }),
          t("Every feature has a deterministic path first, then an AI-augmented path when the API key exists.", { name: "solution-claim", size: 54, bold: true, color: colors.ink, width: wrap(1040), lineSpacingMultiple: 1.0 }),
          t("That means demos, tests, and a fresh clone are not held hostage by external services.", { name: "solution-caption", size: 27, color: colors.muted, width: wrap(980) }),
        ]),
        column({ width: fill, height: fill, gap: 20, justify: "center" }, [
          stage("1. Query", "User asks about a compound, interaction, target class, or generated candidate.", colors.blue),
          stage("2. Reason", "Service layer resolves knowledge-base facts and computes local rankings.", colors.teal),
          stage("3. Augment", "OpenAI adds interpretation when configured; fallback remains explicit.", colors.violet),
          stage("4. Record", "Feedback logs keep experiment outcomes tied to the workflow.", colors.amber),
        ]),
      ],
    ),
    notes: "Describe the split between deterministic domain services and optional LLM enrichment. The system should feel robust even in a low-connectivity or no-key environment.",
  });

  contentSlide(presentation, {
    eyebrow: "03 / ARCHITECTURE",
    title: "The architecture separates product runtime from distributed-agent experiments.",
    subtitle: "The dashboard can run immediately, while uAgents remain available for networked deployments.",
    body: column({ name: "architecture-flow", width: fill, height: fill, gap: 26, justify: "center" }, [
      row({ width: fill, height: hug, gap: 24 }, [
        stage("React frontend", "Dashboard, graph view, forms, result panels", colors.blue),
        stage("Flask API", "HTTP validation, JSON responses, tracing headers", colors.teal),
        stage("Services", "Compound, reaction, research, analysis, DB, LLM, feedback", colors.mint),
      ]),
      row({ width: fill, height: hug, gap: 24 }, [
        stage("MeTTa KB", "Catalyst/enzyme facts, similarity, interactions", colors.amber),
        stage("OpenAI API", "Primary narrative analysis and candidate generation", colors.violet),
        stage("Local fallback", "Deterministic rankings and explainable generated variants", colors.coral),
      ]),
      panel(
        { name: "optional-runtime-band", width: fill, height: fixed(132), padding: { x: 34, y: 24 }, borderRadius: 22, fill: "#EAF2EC", line: { color: "#C8D8CE", width: 1 } },
        row({ width: fill, height: fill, align: "center", gap: 30 }, [
          chip("optional", colors.dark, { name: "optional-chip" }),
          t("uAgents Bureau can run the same service logic as standalone distributed agents, but it is not required for the default app.", { name: "optional-copy", size: 27, bold: true, color: colors.slate, width: fill }),
        ]),
      ),
    ]),
    notes: "Explain that this is the key reliability decision: local direct-service Flask is the default runtime. uAgents are kept as a deployment path rather than a startup dependency.",
  });

  contentSlide(presentation, {
    eyebrow: "04 / CAPABILITIES",
    title: "The platform covers the core loop from profile to decision to feedback.",
    subtitle: "Each capability maps to one service, one API route, and a visible UI behavior.",
    body: grid(
      { name: "capability-grid", width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 28, rowGap: 28 },
      [
        serviceNode("Compound profiling", "Properties, categories, targets, similar compounds", colors.teal),
        serviceNode("Interaction analysis", "Shared targets, explicit risks, warnings", colors.coral),
        serviceNode("Candidate discovery", "Target class, similarity, activity, selectivity filters", colors.blue),
        serviceNode("Ranking", "Activity, selectivity, stability, molecular weight", colors.amber),
        serviceNode("External lookup", "PubChem properties and synonyms", colors.violet),
        serviceNode("Feedback loop", "Experiment records for later review", colors.mint),
      ],
    ),
    notes: "Walk left to right: the app is not only an LLM wrapper. It has a service-per-capability structure that can be tested and extended.",
  });

  contentSlide(presentation, {
    eyebrow: "05 / AI RUNTIME",
    title: "OpenAI is the primary intelligence layer, not the only way the app works.",
    subtitle: "The user gets richer interpretation with a key, and an honest local answer without one.",
    body: grid(
      { name: "runtime-grid", width: fill, height: fill, columns: [fr(1), fr(1)], columnGap: 56 },
      [
        panel(
          { name: "openai-path", width: fill, height: fixed(570), padding: 42, borderRadius: 28, fill: colors.white, line: { color: colors.teal, width: 4 } },
          column({ width: fill, height: fill, gap: 26 }, [
            chip("OPENAI PRIMARY", colors.teal, { name: "openai-chip", width: fixed(220) }),
            t("Compound, interaction, and discovery results can be augmented with model-generated summaries, rankings, and rationale.", { name: "openai-copy", size: 34, bold: true, color: colors.ink, width: fill }),
            t("Default model is configurable through environment variables, so deployment can adapt as model access changes.", { name: "openai-note", size: 23, color: colors.muted, width: fill }),
          ]),
        ),
        panel(
          { name: "fallback-path", width: fill, height: fixed(570), padding: 42, borderRadius: 28, fill: "#EFF5F0", line: { color: colors.amber, width: 4 } },
          column({ width: fill, height: fill, gap: 26 }, [
            chip("LOCAL FALLBACK", colors.amber, { name: "fallback-chip", width: fixed(210), textColor: colors.dark }),
            t("When the key is missing, quota-limited, or unavailable, local KB reasoning still returns useful profiles and candidates.", { name: "fallback-copy", size: 34, bold: true, color: colors.ink, width: fill }),
            t("Responses explicitly report mode and fallback reason instead of hiding degradation.", { name: "fallback-note", size: 23, color: colors.muted, width: fill }),
          ]),
        ),
      ],
    ),
    notes: "Make clear that OpenAI is central to the desired experience, but the product does not collapse without it. This also makes testing dramatically easier.",
  });

  contentSlide(presentation, {
    eyebrow: "06 / AGENT LAYER",
    title: "Seven specialized agents wrap one shared service layer.",
    subtitle: "The wrappers are thin. The business logic stays in reusable, importable modules.",
    body: grid(
      { name: "agent-table", width: fill, height: fill, columns: [fr(0.85), fr(1.25), fr(1.1)], rows: [auto, auto, auto, auto, auto, auto, auto, auto], columnGap: 18, rowGap: 14 },
      [
        t("Agent", { name: "hdr-agent", size: 20, bold: true, color: colors.teal }),
        t("Job", { name: "hdr-job", size: 20, bold: true, color: colors.teal }),
        t("Backed by", { name: "hdr-backed", size: 20, bold: true, color: colors.teal }),
        t("CompoundAgent", { name: "agent-1", size: 25, bold: true }),
        t("Profiles molecules from the knowledge base", { name: "job-1", size: 24, color: colors.slate }),
        t("CompoundService", { name: "svc-1", size: 24, color: colors.muted }),
        t("ReactionAgent", { name: "agent-2", size: 25, bold: true }),
        t("Simulates interaction risk and warnings", { name: "job-2", size: 24, color: colors.slate }),
        t("ReactionService", { name: "svc-2", size: 24, color: colors.muted }),
        t("ResearchAgent", { name: "agent-3", size: 25, bold: true }),
        t("Finds candidates using filters", { name: "job-3", size: 24, color: colors.slate }),
        t("ResearchService", { name: "svc-3", size: 24, color: colors.muted }),
        t("AnalysisAgent", { name: "agent-4", size: 25, bold: true }),
        t("Ranks and summarizes candidate sets", { name: "job-4", size: 24, color: colors.slate }),
        t("AnalysisService", { name: "svc-4", size: 24, color: colors.muted }),
        t("DatabaseAgent", { name: "agent-5", size: 25, bold: true }),
        t("Fetches PubChem compound metadata", { name: "job-5", size: 24, color: colors.slate }),
        t("DatabaseService", { name: "svc-5", size: 24, color: colors.muted }),
        t("LLMAgent", { name: "agent-6", size: 25, bold: true }),
        t("Adds OpenAI analysis and candidate generation", { name: "job-6", size: 24, color: colors.slate }),
        t("LLMService", { name: "svc-6", size: 24, color: colors.muted }),
        t("FeedbackAgent", { name: "agent-7", size: 25, bold: true }),
        t("Persists experiment feedback", { name: "job-7", size: 24, color: colors.slate }),
        t("FeedbackService", { name: "svc-7", size: 24, color: colors.muted }),
      ],
    ),
    notes: "This slide should reassure technical reviewers: agents are not duplicating logic. They are adapters around the same tested service classes used by Flask.",
  });

  contentSlide(presentation, {
    eyebrow: "07 / DEMO FLOW",
    title: "A useful run starts with HZSM_5 and ends with a ranked, explainable action.",
    subtitle: "The flow is short enough for a demo, but grounded enough for a product conversation.",
    body: grid(
      { name: "demo-grid", width: fill, height: fill, columns: [fr(0.72), fr(1.28)], columnGap: 54 },
      [
        panel(
          { name: "demo-input", width: fill, height: fixed(560), padding: 40, borderRadius: 28, fill: colors.dark },
          column({ width: fill, height: fill, gap: 24, justify: "center" }, [
            t("Example input", { name: "demo-input-label", size: 22, bold: true, color: colors.mint }),
            t("Find enzyme or catalyst candidates with high selectivity.", { name: "demo-input-copy", size: 44, bold: true, color: colors.white, width: fill, lineSpacingMultiple: 1.02 }),
            chip("base: HZSM_5", colors.mint, { name: "demo-chip", textColor: colors.dark }),
          ]),
        ),
        column({ name: "demo-steps", width: fill, height: fill, gap: 14, justify: "center" }, [
          stage("Resolve profile", "Properties, categories, targets, interactions", colors.teal, 112, 17),
          stage("Discover candidates", "Filter by class, similarity, activity, or selectivity", colors.blue, 124, 16),
          stage("Rank evidence", "Sort by selected criterion and expose skipped fields", colors.amber, 112, 17),
          stage("Add interpretation", "OpenAI analysis if available; local fallback otherwise", colors.violet, 124, 16),
          stage("Log outcome", "Save feedback for review", colors.coral, 124, 17),
        ]),
      ],
    ),
    notes: "Use this as the live demo script. The important part is that each step is visible and maps to a service and route.",
  });

  contentSlide(presentation, {
    eyebrow: "08 / RELIABILITY",
    title: "The repaired project now has checks for the failure that triggered this review.",
    subtitle: "The point is not that tests exist. The point is that they cover startup, routing, fallback, and missing-domain errors.",
    body: grid(
      { name: "reliability-grid", width: fill, height: fill, columns: [fr(1), fr(1)], columnGap: 54 },
      [
        column({ name: "reliability-copy", width: fill, height: fill, gap: 28, justify: "center" }, [
          openBullet("Committed service layer", "`services/` is part of the tree and imported by both Flask and agent wrappers.", colors.teal),
          openBullet("Direct startup path", "The Flask backend no longer requires a separate Bureau for the dashboard to run.", colors.blue),
          openBullet("Graceful degradation", "OpenAI failures route to explicit local fallback instead of blank or misleading output.", colors.amber),
        ]),
        panel(
          { name: "test-proof", width: fill, height: fixed(545), padding: 40, borderRadius: 30, fill: colors.white, line: { color: "#D4DED6", width: 1 } },
          column({ width: fill, height: fill, gap: 22, justify: "center" }, [
            t("Validation passed", { name: "validation-label", size: 22, bold: true, color: colors.teal }),
            t("Backend tests, compile sweep, frontend build, and HTTP health smoke.", { name: "validation-main", size: 43, bold: true, color: colors.ink, width: fill, lineSpacingMultiple: 1.03 }),
            rule({ width: fixed(420), stroke: colors.teal, weight: 5 }),
            t("Regression tests cover `/health`, compound lookup, discovery ranking, local generation, and unknown-molecule 404.", { name: "validation-note", size: 23, color: colors.muted, width: fill }),
          ]),
        ),
      ],
    ),
    notes: "This is where you can confidently answer: yes, it works locally, and the current main tree includes services. Mention that tests should be committed and kept as a guardrail.",
  });

  contentSlide(presentation, {
    eyebrow: "10 / IMPACT AND NEXT STEPS",
    title: "The next version should be harder to break and easier to prove.",
    subtitle: "Impact comes from faster screening, visible reasoning, and a deployment path that survives a fresh clone.",
    body: grid(
      { name: "next-grid", width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], columnGap: 28 },
      [
        panel(
          { name: "next-1", width: fill, height: fixed(430), padding: 34, borderRadius: 28, fill: colors.white, line: { color: "#D4DED6", width: 1 } },
          column({ width: fill, height: fill, gap: 20 }, [
            chip("Data", colors.blue, { name: "next-data" }),
            t("Expand the knowledge base", { name: "next-data-title", size: 36, bold: true, color: colors.ink }),
            t("Add richer catalyst, enzyme, condition, yield, stability, and provenance fields.", { name: "next-data-copy", size: 24, color: colors.muted }),
          ]),
        ),
        panel(
          { name: "next-2", width: fill, height: fixed(430), padding: 34, borderRadius: 28, fill: colors.white, line: { color: "#D4DED6", width: 1 } },
          column({ width: fill, height: fill, gap: 20 }, [
            chip("Learning", colors.teal, { name: "next-learning" }),
            t("Use feedback as evidence", { name: "next-learning-title", size: 36, bold: true, color: colors.ink }),
            t("Turn experiment logs into calibration data instead of a passive audit trail.", { name: "next-learning-copy", size: 24, color: colors.muted }),
          ]),
        ),
        panel(
          { name: "next-3", width: fill, height: fixed(430), padding: 34, borderRadius: 28, fill: colors.white, line: { color: "#D4DED6", width: 1 } },
          column({ width: fill, height: fill, gap: 20 }, [
            chip("Deployment", colors.amber, { name: "next-deploy", textColor: colors.dark }),
            t("Prove fresh-clone reliability", { name: "next-deploy-title", size: 36, bold: true, color: colors.ink }),
            t("Run CI on backend tests, frontend build, import checks, and API smoke tests.", { name: "next-deploy-copy", size: 24, color: colors.muted }),
          ]),
        ),
      ],
    ),
    notes: "Close with practical engineering and science improvements. The strongest next proof is a clean fresh clone plus CI, then richer domain data and feedback learning.",
  });

  return presentation;
}

async function saveBlob(blob, filePath) {
  const buffer = Buffer.from(await blob.arrayBuffer());
  await fs.writeFile(filePath, buffer);
}

async function exportPreviews(presentation, prefix) {
  const files = [];
  for (let i = 0; i < presentation.slides.count; i += 1) {
    const slide = presentation.slides.getItem(i);
    const blob = await slide.export({ format: "png", scale: 1 });
    const pngPath = `${PREVIEWS}/${prefix}_slide_${String(i + 1).padStart(2, "0")}.png`;
    await saveBlob(blob, pngPath);
    files.push(pngPath);

    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(
      `${PREVIEWS}/${prefix}_slide_${String(i + 1).padStart(2, "0")}.layout.json`,
      JSON.stringify(layout, null, 2),
    );
  }
  return files;
}

const presentation = makeDeck();
const pptxBlob = await PresentationFile.exportPptx(presentation);
await pptxBlob.save(PPTX);

const sourcePreviews = await exportPreviews(presentation, "source");

let pptxParity = { ok: false, previews: [], error: null };
try {
  const bytes = await fs.readFile(PPTX);
  const imported = await PresentationFile.importPptx(bytes);
  const savedPreviews = await exportPreviews(imported, "saved_pptx");
  pptxParity = { ok: true, previews: savedPreviews, error: null };
} catch (error) {
  pptxParity = { ok: false, previews: [], error: String(error?.stack ?? error) };
}

const manifest = {
  pptx: path.resolve(PPTX),
  sourcePreviews: sourcePreviews.map((p) => path.resolve(p)),
  pptxParity,
  slideCount: presentation.slides.count,
};

await fs.writeFile(`${OUT}/manifest.json`, JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
