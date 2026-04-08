---
title: "Gary King"
type: landing

sections:
  - block: hero
    content:
      title: "Gary King"
      text: "Albert J. Weatherhead III University Professor at Harvard University and Director of the Institute for Quantitative Social Science. He develops and applies empirical methods in many areas of social science, focusing on innovations that span the range from statistical theory to practical application."
      primary_action:
        text: Bio & CV
        url: /bio/
      secondary_action:
        text: Publications
        url: /publication/
    design:
      background:
        image:
          filename: images/gary-hp-image.jpg
          parallax: false
          position: center
          size: cover

  - block: markdown
    content:
      title: ""
      text: |
        <div style="display:flex;gap:2rem;justify-content:center;flex-wrap:wrap;margin:2rem 0;">
          <div style="text-align:center;">
            <img src="/gking-site/images/statistical-icon.png" alt="Statistical Methods" style="width:64px;height:64px;">
            <p style="font-size:0.85rem;margin-top:0.5rem;"><strong>190+</strong> Journal Articles</p>
          </div>
          <div style="text-align:center;">
            <img src="/gking-site/images/people-icon.png" alt="Collaborators" style="width:64px;height:64px;">
            <p style="font-size:0.85rem;margin-top:0.5rem;"><strong>8</strong> Honorary Societies</p>
          </div>
          <div style="text-align:center;">
            <img src="/gking-site/images/papers-orange.png" alt="Papers" style="width:64px;height:auto;">
            <p style="font-size:0.85rem;margin-top:0.5rem;"><strong>55+</strong> Awards</p>
          </div>
          <div style="text-align:center;">
            <img src="/gking-site/images/books-orange.png" alt="Books" style="width:64px;height:auto;">
            <p style="font-size:0.85rem;margin-top:0.5rem;"><strong>8</strong> Books</p>
          </div>
          <div style="text-align:center;">
            <img src="/gking-site/images/presos-orange.png" alt="Software" style="width:64px;height:auto;">
            <p style="font-size:0.85rem;margin-top:0.5rem;"><strong>30+</strong> Software Packages</p>
          </div>
        </div>

  - block: collection
    content:
      title: Recent Publications
      count: 10
      filters:
        folders:
          - publication
    design:
      view: citation

  - block: collection
    content:
      title: Recent Presentations
      count: 5
      filters:
        folders:
          - talk
    design:
      view: date-title-summary

  - block: markdown
    content:
      title: Video Presentations
      text: |
        <div style="max-width:720px;margin:0 auto 2rem;">
          <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">
            <iframe src="https://www.youtube.com/embed/piyOAcUq2mU" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen title="Interview with Gary King on Science and Inference"></iframe>
          </div>
          <p style="text-align:center;margin-top:0.75rem;font-size:0.9rem;color:#666;">Interview with Gary King on Science and Inference</p>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;margin-top:2rem;">
          <a href="https://www.youtube.com/playlist?list=PL0n492lUg2sg9atDiK-ysPF43Wotuk4TU" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;">
            <div style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;transition:box-shadow 0.2s;">
              <img src="/gking-site/images/garythumbnail_3.jpg" alt="Research Talks" style="width:100%;display:block;">
              <div style="padding:0.75rem 1rem;">
                <strong>Research Talks by Gary King</strong><br>
                <span style="font-size:0.85rem;color:#666;">Recorded by me</span>
              </div>
            </div>
          </a>
          <a href="https://www.youtube.com/playlist?list=PL0n492lUg2sjYNAtpfatEm-AuGkAmCz4G" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;">
            <div style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;transition:box-shadow 0.2s;">
              <img src="/gking-site/images/garythumbnail_seminar.jpg" alt="Research Talks by Others" style="width:100%;display:block;">
              <div style="padding:0.75rem 1rem;">
                <strong>Research Talks by Gary King</strong><br>
                <span style="font-size:0.85rem;color:#666;">Recorded by others</span>
              </div>
            </div>
          </a>
          <a href="https://www.youtube.com/playlist?list=PL0n492lUg2sgSevEQ3bLilGbFph4l92gH" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;">
            <div style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;transition:box-shadow 0.2s;">
              <img src="/gking-site/images/garythumbnail_lecture.jpg" alt="Lectures" style="width:100%;display:block;">
              <div style="padding:0.75rem 1rem;">
                <strong>Lectures for QSS Methods I</strong><br>
                <span style="font-size:0.85rem;color:#666;">Full course playlist</span>
              </div>
            </div>
          </a>
        </div>

  - block: collection
    content:
      title: Software
      count: 10
      filters:
        folders:
          - software
    design:
      view: card
---
