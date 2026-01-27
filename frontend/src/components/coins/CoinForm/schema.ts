
import { z } from "zod"
import { DomainCoinSchema } from "@/domain/schemas"

// Schema for form values
export const CreateCoinSchema = DomainCoinSchema.omit({ id: true }).extend({
    rarity: z.preprocess((val) => val === "" ? null : val, DomainCoinSchema.shape.rarity)
}).superRefine((data, ctx) => {
    if (data.attribution.year_start != null && data.attribution.year_end != null) {
        if (data.attribution.year_end < data.attribution.year_start) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "End year must be after start year",
                path: ["attribution", "year_end"],
            });
        }
    }
});

export type CoinFormData = z.infer<typeof CreateCoinSchema>;
