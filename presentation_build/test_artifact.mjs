const {
  Presentation,
  PresentationFile,
  column,
  text,
  fill,
  hug,
} = await import("file:///C:/Users/aacer/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs");

const presentation = Presentation.create({ slideSize: { width: 1920, height: 1080 } });
const slide = presentation.slides.add();
slide.compose(
  column(
    { name: "root", width: fill, height: fill, padding: 80, gap: 24 },
    [
      text("BioAgents", { name: "title", width: fill, height: hug, style: { fontSize: 96, bold: true, color: "#10201D" } }),
      text("test", { name: "subtitle", width: fill, height: hug, style: { fontSize: 36, color: "#2F4C46" } }),
    ],
  ),
  { frame: { left: 0, top: 0, width: 1920, height: 1080 }, baseUnit: 8 },
);

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save("presentation_build/output/test.pptx");
const png = await slide.export({ format: "png", scale: 1 });
await png.save("presentation_build/previews/test.png");
