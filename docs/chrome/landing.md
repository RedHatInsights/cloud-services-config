# Landing page navigation schema

```TS
interface LandingPageItem {
  title: string // Title of the link
  href: string // absolute pathname of link
  id: string // unique id
}

type LandingPageSchema = LandingPageItem[]
```