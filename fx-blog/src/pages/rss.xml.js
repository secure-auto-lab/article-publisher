import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const posts = (await getCollection('posts', ({ data }) => !data.draft)).sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
  );

  return rss({
    title: 'secure-auto-lab FXラボ',
    description:
      'FXで5回以上口座をゼロにした会社員が、AIと敗因を数字で解剖し、自動売買を作り直すまでの検証記録。',
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/posts/${post.id}/`,
    })),
    customData: '<language>ja</language>',
  });
}
