import { describe, expect, it } from "vitest";

import { cn, formatUzPhone, maskPhone, uzPhoneToE164 } from "./utils";

describe("cn", () => {
  it("merges class names and resolves Tailwind conflicts", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-red-500", undefined, "font-bold")).toBe("text-red-500 font-bold");
  });
});

describe("maskPhone", () => {
  it("masks middle digits", () => {
    expect(maskPhone("+998901234567")).toBe("+998***67");
  });

  it("returns short input unchanged", () => {
    expect(maskPhone("+998")).toBe("+998");
  });
});

describe("formatUzPhone", () => {
  it("formats 9-digit local number with +998 prefix", () => {
    expect(formatUzPhone("901234567")).toBe("+998 90 123 45 67");
  });

  it("strips existing +998", () => {
    expect(formatUzPhone("+998901234567")).toBe("+998 90 123 45 67");
  });

  it("returns +998 prefix for empty input", () => {
    expect(formatUzPhone("")).toBe("+998 ");
  });
});

describe("uzPhoneToE164", () => {
  it("strips formatting and adds +", () => {
    expect(uzPhoneToE164("+998 90 123 45 67")).toBe("+998901234567");
  });

  it("adds 998 prefix when missing", () => {
    expect(uzPhoneToE164("901234567")).toBe("+998901234567");
  });
});
