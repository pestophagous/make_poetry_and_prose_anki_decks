#!/bin/bash

set -Eeuxo pipefail # https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

TESTTMPFILE=/tmp/prose_anki_tests.txt

rm -f ${TESTTMPFILE}

${THISDIR}/upload_deck_for_single_text.py -s ma ${THISDIR}/sample_input/mañanitas.txt > ${TESTTMPFILE}

# Our goal is to see NO DIFFERENCE.
# When `diff` sees no difference, it returns 0 (good for us).
# If any other return code is returned, our script fails (due to set -e),
#   ... which is exactly what we want.
diff ${THISDIR}/sample_output/mañanitas_01.txt ${TESTTMPFILE}

echo 'We assume this was run with '\''set -e'\'' (look at upper lines of this script).'
echo 'Assuming so, then getting here means:'
echo 'run_all_tests.sh SUCCESS'
