# GitHub setup — preserving the existing EncyK archive

The GitHub name `Rejean-McCormick/EncyKlopedia` currently belongs to the **old source-acquisition repository**, not to this new encyclopedia. It must not be overwritten.

1. Back up and rename the **old** repository through GitHub's repository Settings → General → Repository name: `EncyK` (or a unique archival name). Preserve its Git history, tags, issues and any related clone remotes. Adjust scripts/links that depend on the old name.
2. Create a **new empty repository**, called `EncyKlopedia`, in the same GitHub account. Choose public/private according to your code-release decision. Do **not** initialize it with a README or license, since this bundle has its own README and no license decision has been made.
3. Unzip the folder `EncyKlopedia/` locally and, in that folder, use:

   ```bash
   git init -b main
   git add .
   git commit -m "Bootstrap EncyKlopedia public reader alpha"
   git remote add origin https://github.com/Rejean-McCormick/EncyKlopedia.git
   git push -u origin main
   ```

4. Check GitHub Actions CI. Do not push any real corpus, extracts, access tokens, Windows `D:` data or unqualified Kristal assets.

**Important:** GitHub URL redirects from the renamed old repository will no longer be a substitute for updating old links once the original `EncyKlopedia` name is used by the new repository. Update affected source links explicitly.

If the official product spelling becomes `Encyclomedia` instead, rename this repo *before* creating it; current files intentionally use the previously agreed **EncyKlopedia** spelling.
