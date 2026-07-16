import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");
const sourcePath = resolve(frontendRoot, "src/assets/india-full-detail.json");
const outputPath = resolve(frontendRoot, "src/assets/india-islands-detail.json");
const islandNames = new Set(["Andaman and Nicobar Islands", "Lakshadweep"]);

const source = JSON.parse(await readFile(sourcePath, "utf8"));
const features = source.features.filter((feature) => islandNames.has(feature.properties?.name));

if (features.length !== islandNames.size) {
  const found = features.map((feature) => feature.properties?.name).sort();
  throw new Error(`Expected ${islandNames.size} island features, found ${features.length}: ${found.join(", ")}`);
}

const output = {
  type: "FeatureCollection",
  features,
};

await writeFile(outputPath, `${JSON.stringify(output)}\n`);
console.log(`Wrote ${features.length} island features to ${outputPath}`);
