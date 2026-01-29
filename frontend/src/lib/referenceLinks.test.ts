import { describe, it, expect } from "vitest";
import {
  formatReference,
  parseReference,
  buildExternalLinks,
  SUPPORTED_CATALOGS_FALLBACK,
  type CatalogReference,
} from "./referenceLinks";

describe("formatReference", () => {
  it("formats catalog + number", () => {
    expect(formatReference({ catalog: "RIC", number: "207" })).toBe("RIC 207");
  });

  it("includes volume when present", () => {
    expect(formatReference({ catalog: "RIC", volume: "II", number: "756" })).toBe("RIC II 756");
  });

  it("includes supplement for RPC", () => {
    expect(
      formatReference({ catalog: "RPC", volume: "I", supplement: "S", number: "123" })
    ).toBe("RPC I S 123");
  });

  it("includes mint for RIC", () => {
    expect(
      formatReference({ catalog: "RIC", volume: "VII", mint: "Ticinum", number: "123" })
    ).toBe("RIC VII Ticinum 123");
  });

  it("includes collection for SNG", () => {
    expect(
      formatReference({ catalog: "SNG", collection: "Cop", number: "123" })
    ).toBe("SNG Cop 123");
  });

  it("builds full display order: catalog, volume, supplement, mint, collection, number", () => {
    const ref: CatalogReference = {
      catalog: "RPC",
      volume: "I",
      supplement: "S2",
      number: "456",
    };
    expect(formatReference(ref)).toBe("RPC I S2 456");
  });
});

describe("parseReference", () => {
  it("returns null for empty or whitespace", () => {
    expect(parseReference("")).toBeNull();
    expect(parseReference("   ")).toBeNull();
  });

  it("parses RIC with volume", () => {
    const r = parseReference("RIC II 118");
    expect(r).not.toBeNull();
    expect(r!.catalog).toBe("RIC");
    expect(r!.volume).toBe("II");
    expect(r!.number).toBe("118");
  });

  it("parses RIC with volume and mint", () => {
    const r = parseReference("RIC VII Ticinum 123");
    expect(r).not.toBeNull();
    expect(r!.catalog).toBe("RIC");
    expect(r!.volume).toBe("VII");
    expect(r!.mint).toBe("Ticinum");
    expect(r!.number).toBe("123");
  });

  it("parses RPC with volume and optional supplement", () => {
    const r1 = parseReference("RPC I 4122");
    expect(r1).not.toBeNull();
    expect(r1!.catalog).toBe("RPC");
    expect(r1!.volume).toBe("I");
    expect(r1!.number).toBe("4122");

    const r2 = parseReference("RPC I S 123");
    expect(r2).not.toBeNull();
    expect(r2!.supplement).toBe("S");
    expect(r2!.number).toBe("123");
  });

  it("parses Crawford and RRC as RRC", () => {
    const c = parseReference("Crawford 335/1c");
    expect(c).not.toBeNull();
    expect(c!.catalog).toBe("RRC");
    expect(c!.number).toBe("335/1c");

    const r = parseReference("RRC 494/43");
    expect(r).not.toBeNull();
    expect(r!.catalog).toBe("RRC");
    expect(r!.number).toBe("494/43");
  });

  it("parses SNG with collection", () => {
    const r = parseReference("SNG Cop 123");
    expect(r).not.toBeNull();
    expect(r!.catalog).toBe("SNG");
    expect(r!.collection).toBe("Cop");
    expect(r!.number).toBe("123");
  });

  it("parses DOC with volume", () => {
    const r = parseReference("DOC III 100");
    expect(r).not.toBeNull();
    expect(r!.catalog).toBe("DOC");
    expect(r!.volume).toBe("III");
    expect(r!.number).toBe("100");
  });

  it("parses simple format (Sear, Cohen, BMCRR)", () => {
    expect(parseReference("Sear 3124")!.catalog).toBe("Sear");
    expect(parseReference("Sear 3124")!.number).toBe("3124");
    expect(parseReference("Cohen 382")!.catalog).toBe("Cohen");
    expect(parseReference("BMCRR 100")!.catalog).toBe("BMCRR");
  });

  it("returns null for unrecognized format", () => {
    expect(parseReference("RandomText")).toBeNull();
    expect(parseReference("123 only numbers")).toBeNull();
  });
});

describe("buildExternalLinks", () => {
  it("returns empty array for empty references", () => {
    expect(buildExternalLinks([])).toEqual([]);
  });

  it("adds OCRE link for RIC references", () => {
    const links = buildExternalLinks([
      { catalog: "RIC", volume: "II", number: "118" },
    ]);
    const ocre = links.find((l) => l.name === "OCRE");
    expect(ocre).toBeDefined();
    expect(ocre!.validated).toBe(true);
    expect(ocre!.url).toContain("numismatics.org/ocre");
  });

  it("adds CRRO link for RRC references", () => {
    const links = buildExternalLinks([
      { catalog: "RRC", number: "335/1c" },
    ]);
    const crro = links.find((l) => l.name === "CRRO");
    expect(crro).toBeDefined();
    expect(crro!.validated).toBe(true);
    expect(crro!.url).toContain("numismatics.org/crro");
  });

  it("adds RPC Online link for RPC references", () => {
    const links = buildExternalLinks([
      { catalog: "RPC", volume: "I", number: "1234" },
    ]);
    const rpc = links.find((l) => l.name === "RPC Online");
    expect(rpc).toBeDefined();
    expect(rpc!.validated).toBe(true);
    expect(rpc!.url).toContain("rpc.ashmus.ox.ac.uk");
  });

  it("includes general search links when references exist", () => {
    const links = buildExternalLinks([
      { catalog: "Sear", number: "3124" },
    ]);
    expect(links.some((l) => l.name === "ACSearch")).toBe(true);
    expect(links.some((l) => l.name === "Wildwinds")).toBe(true);
  });

  it("uses formatReference for search query (RPC I S 123)", () => {
    const links = buildExternalLinks([
      { catalog: "RPC", volume: "I", supplement: "S", number: "123" },
    ]);
    const rpc = links.find((l) => l.name === "RPC Online");
    expect(rpc!.url).toContain(encodeURIComponent("RPC I S 123"));
  });
});

describe("SUPPORTED_CATALOGS_FALLBACK", () => {
  it("includes expected catalogs", () => {
    expect(SUPPORTED_CATALOGS_FALLBACK).toContain("RIC");
    expect(SUPPORTED_CATALOGS_FALLBACK).toContain("RRC");
    expect(SUPPORTED_CATALOGS_FALLBACK).toContain("DOC");
    expect(SUPPORTED_CATALOGS_FALLBACK).toContain("SNG");
    expect(SUPPORTED_CATALOGS_FALLBACK).toContain("Calicó");
  });

  it("is non-empty", () => {
    expect(SUPPORTED_CATALOGS_FALLBACK.length).toBeGreaterThan(0);
  });
});
