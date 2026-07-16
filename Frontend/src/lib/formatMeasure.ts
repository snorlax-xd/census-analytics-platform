const categoryDisplayNames: Record<string, string> = {
  demographics: "Demographics",
  economy: "Economy",
  literacy: "Literacy",
  infrastructure: "Infrastructure",
  sanitation: "Sanitation",
  drinking_water: "Drinking Water",
};

const acronymWords = new Set(["SC", "ST", "LPG", "PNG"]);

function titleCase(value: string) {
  return value
    .replace(/_/g, " ")
    .trim()
    .split(/\s+/)
    .map((word) => {
      const upper = word.toUpperCase();

      if (acronymWords.has(upper)) {
        return upper;
      }

      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(" ");
}

export function formatCategoryName(category: string) {
  return categoryDisplayNames[category] ?? titleCase(category);
}

export function formatMeasureName(measureCode: string, measureName?: string) {
  const displayName = measureName?.trim();

  if (displayName) {
    return displayName;
  }

  return titleCase(measureCode);
}
