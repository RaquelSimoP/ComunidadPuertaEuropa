// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import vercel from '@astrojs/vercel';

// https://astro.build/config
export default defineConfig({
	adapter: vercel({
		webAnalytics: { enabled: true }
	}),
	integrations: [
		starlight({
			title: 'Comunidad Puerta Europa',
			social: [],
			sidebar: [],
		}),
	],
});
