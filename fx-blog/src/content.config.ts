import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/[^_]*.{md,mdx}', base: './src/content/posts' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    series: z.string().default('全損から始める自動売買'),
    seriesIndex: z.number(),
    paid: z.boolean().default(false),
    hasPromotion: z.boolean().default(false),
    heroImage: z.string().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

// 日次運用記（src.fx_daily パイプラインが自動生成。スキーマ変更時はパイプライン側と同期）
const daily = defineCollection({
  loader: glob({ pattern: '**/[^_]*.{md,mdx}', base: './src/content/daily' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    judgment: z.enum(['normal', 'L1', 'L2', 'L3']),
    judgmentLabel: z.string(),
    approved: z.boolean().default(false),
    llmGenerated: z.boolean().default(false),
    figure: z.string(),
    metrics: z.object({
      dayPips: z.number(),
      dayJpy: z.number(),
      mtdJpy: z.number(),
      totalJpy: z.number(),
      totalPct: z.number(),
      drawdownPct: z.number(),
    }),
    signals: z.object({
      detected: z.number(),
      skippedZ: z.number(),
      skippedSpread: z.number(),
      entered: z.number(),
      entriesByZ: z.record(z.string(), z.number()).optional(),
    }),
    slippage: z.object({
      measuredPips: z.number().nullable(),
      assumptionPips: z.number(),
      samples: z.number(),
    }),
    judgmentReasons: z.array(z.string()).default([]),
  }),
});

export const collections = { posts, daily };
