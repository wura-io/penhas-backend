require('ts-node').register({
  transpileOnly: true,
  compilerOptions: {
    module: 'commonjs'
  }
});

module.exports = {
  // Gherkin feature files
  default: '--require-module ts-node/register --require step-definitions/world.ts --require step-definitions/hooks.ts --require step-definitions/api-steps.ts --require step-definitions/db-steps.ts --require support/global-hooks.ts --require support/testcontainers.ts --require support/perl-api-manager.ts --format progress --format html:reports/report.html --format json:reports/report.json --tags "not @wip"'
};

