export type LocaleMeta = {
  code: string;
  name: string;
};

export const locales: LocaleMeta[] = [
  { code: "JK", name: "Jammu and Kashmir" },
  { code: "HP", name: "Himachal Pradesh" },
  { code: "PB", name: "Punjab" },
  { code: "CH", name: "Chandigarh" },
  { code: "UK", name: "Uttarakhand" },
  { code: "HR", name: "Haryana" },
  { code: "DL", name: "Delhi" },
  { code: "RJ", name: "Rajasthan" },
  { code: "UP", name: "Uttar Pradesh" },
  { code: "BR", name: "Bihar" },
  { code: "SK", name: "Sikkim" },
  { code: "AR", name: "Arunachal Pradesh" },
  { code: "NL", name: "Nagaland" },
  { code: "MN", name: "Manipur" },
  { code: "MZ", name: "Mizoram" },
  { code: "TR", name: "Tripura" },
  { code: "ML", name: "Meghalaya" },
  { code: "AS", name: "Assam" },
  { code: "WB", name: "West Bengal" },
  { code: "JH", name: "Jharkhand" },
  { code: "OD", name: "Odisha" },
  { code: "CT", name: "Chhattisgarh" },
  { code: "MP", name: "Madhya Pradesh" },
  { code: "GJ", name: "Gujarat" },
  { code: "DD", name: "Daman and Diu" },
  { code: "DN", name: "Dadra and Nagar Haveli" },
  { code: "MH", name: "Maharashtra" },
  { code: "AP", name: "Andhra Pradesh" },
  { code: "KA", name: "Karnataka" },
  { code: "GA", name: "Goa" },
  { code: "LD", name: "Lakshadweep" },
  { code: "KL", name: "Kerala" },
  { code: "TN", name: "Tamil Nadu" },
  { code: "PY", name: "Puducherry" },
  { code: "AN", name: "Andaman and Nicobar Islands" },
];

export const localeCodes = locales.map((locale) => locale.code);

export const localeCodeByName = new Map([
  ...locales.map((locale) => [locale.name, locale.code] as const),
  ["NCT of Delhi", "DL"],
]);
