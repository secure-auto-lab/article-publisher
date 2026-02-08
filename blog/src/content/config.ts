import { defineCollection, z } from 'astro:content';

const categories = ['automation', 'ai', 'security', 'dev-tips', 'projects', 'web', 'infrastructure'] as const;

const articles = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    category: z.enum(categories).default('dev-tips'),
    tags: z.array(z.string()).optional(),
    author: z.string().default('secure＆autoラボ'),
    heroImage: z.string().optional(),
    // Monetization
    noteUrl: z.string().optional(), // Link to paid Note article
    amazonProducts: z.array(z.object({
      asin: z.string(),
      title: z.string(),
      image: z.string().optional(),
      price: z.string().optional(),
    })).optional(),
  }),
});

export const collections = {
  articles,
};

export { categories };
