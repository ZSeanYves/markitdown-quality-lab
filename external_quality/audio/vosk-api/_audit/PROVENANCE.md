# Audio Provenance

Source group: `external_quality/audio/vosk-api`

Upstream source:

- Repository: `alphacep/vosk-api`
- URL: `https://github.com/alphacep/vosk-api`
- License: Apache-2.0
- Official sample path: `python/example/test.wav`
- Official license mirror retained from upstream `COPYING`

Retained samples:

- `vosk_test_official.wav`
  - origin: direct byte capture of upstream `python/example/test.wav`
  - github blob sha noted by API at intake: `c41144a21710590e568e4e612d2a40baf9a71223`
  - sha256: `dcfea5712c43a43ba7ae8083afb39d36993e5a69c46e88b68aaa72b65cb615bb`
- `vosk_test_official.mp3`
  - origin: locally transcoded from retained `vosk_test_official.wav`
  - command class: `ffmpeg -codec:a libmp3lame`
  - sha256: `d6ea5e591861fb30e1ed4ce84cdb4c9a0125b8ea01bd99d35b427cc23b39fa87`
- `vosk_test_official.m4a`
  - origin: locally transcoded from retained `vosk_test_official.wav`
  - command class: `ffmpeg -c:a aac`
  - sha256: `ce0fb9ce47400eadb8403e9187ea59487f581cedf06769db20e08a109afeda88`

Intake notes:

- The upstream repository and sample bytes were accessed through GitHub API and
  raw GitHub endpoints during local intake.
- The compressed derivatives are retained only to cover the `mp3` and `m4a`
  product routes under the same speech content and license umbrella.
- Transcript expectations should be treated as backend-sensitive. Prefer stable
  audio-route and backend evidence in debug/provenance views when exact wording
  would be brittle.
