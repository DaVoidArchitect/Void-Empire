# CONTRIBUTING TO ORIGIN-V OMEGA

**Welcome!** Origin-V Omega is an open-source SoC IP Core. Once released, development continues through community contributions.

---

## 🔄 DEVELOPMENT MODEL

### Open-Source Development
- **Main Repository:** Community-driven development
- **Contributions:** Pull requests welcome
- **Maintainers:** Community maintainers (initial maintainer: Founder)
- **License:** S-OHL (Sovereign Open Hardware License)

### Release Philosophy
- **v2.1 Release:** Production-ready baseline
- **Future Development:** Community enhancements
- **Hard-Law Constants:** Immutable (core economic laws)
- **Everything Else:** Open for improvement

---

## 🚀 GETTING STARTED

### Prerequisites
1. **Simulator:** Verilator, Icarus Verilog, or commercial (VCS/Questa)
2. **SystemVerilog Knowledge:** RTL design experience
3. **Git:** Version control

### Setup Development Environment

1. **Clone Repository**
```bash
git clone <repository-url>
cd Origin-V-Omega
```

2. **Install Simulator** (see SIMULATOR_SETUP.md)

3. **Run Tests**
```bash
# Using Verilator
verilator --cc --exe --build rtl/*.sv tb/tb_grand_core.sv -o sim

# Or using provided scripts
./scripts/run_simulation.sh
```

---

## 📝 CONTRIBUTING GUIDELINES

### Code Standards
- **Language:** SystemVerilog-2012
- **Style:** Follow existing code style
- **Comments:** Comprehensive documentation
- **Synthesizable:** All code must be synthesis-ready

### Testing Requirements
- ✅ All new code must have testbenches
- ✅ All tests must pass
- ✅ Maintain >90% code coverage
- ✅ Update documentation

### Submission Process
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

---

## 🎯 AREAS FOR CONTRIBUTION

### High Priority
- **Verification:** Add more testbenches
- **Performance:** Optimize critical paths
- **Documentation:** Improve guides
- **Examples:** Additional integration examples

### Feature Additions
- **Enhanced AES:** Full inverse operations
- **NoC Optimization:** Better routing algorithms
- **SEU Enhancements:** Additional ISA extensions
- **Power Optimization:** Low-power modes

### Bug Fixes
- Report issues via GitHub Issues
- Fix bugs via Pull Requests
- Test thoroughly before submitting

---

## ⚠️ RESTRICTIONS

### Immutable (Cannot Change)
- **Hard-Law Constants:** 6.18% economic split (etched in silicon concept)
- **Core Architecture:** 11-Stack structure
- **License:** S-OHL terms

### Review Required
- **Interface Changes:** Must maintain backward compatibility
- **Performance Changes:** Must not degrade existing performance
- **Security Changes:** Must be thoroughly reviewed

---

## 📚 DOCUMENTATION

### Required Documentation Updates
When contributing, update:
- **Code Comments:** Inline documentation
- **Architecture Manual:** If architecture changes
- **API Reference:** If interfaces change
- **CHANGELOG.md:** All changes documented

---

## 🧪 TESTING

### Before Submitting PR
```bash
# Run all tests
./scripts/run_all_tests.sh

# Verify linting
verilator --lint-only rtl/*.sv

# Check code coverage
# (Use your simulator's coverage tools)
```

### Test Coverage
- Maintain >90% coverage
- Add tests for new features
- Verify existing tests still pass

---

## 📋 PULL REQUEST TEMPLATE

### PR Title
`[Type]: Brief Description`

Types: `Feature`, `Fix`, `Docs`, `Test`, `Refactor`

### PR Description
- **What:** What does this PR do?
- **Why:** Why is this change needed?
- **Testing:** How was it tested?
- **Impact:** What are the implications?

### Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] No new warnings

---

## 🤝 CODE OF CONDUCT

### Expectations
- **Respectful:** Be professional and respectful
- **Constructive:** Provide helpful feedback
- **Inclusive:** Welcome all contributors
- **Collaborative:** Work together towards goals

### Communication
- **Issues:** Use GitHub Issues for bugs/features
- **Discussions:** Use GitHub Discussions for questions
- **PR Reviews:** Be constructive and helpful

---

## 📖 RESOURCES

### Learning
- **SystemVerilog:** IEEE 1800-2012 standard
- **RISC-V:** RISC-V ISA specifications
- **AES:** FIPS 197 specification
- **NoC Design:** Network-on-Chip literature

### Tools
- **Verilator:** Free SystemVerilog simulator
- **Icarus Verilog:** Free Verilog simulator
- **Yosys:** Free synthesis tool
- **GTKWave:** Free waveform viewer

---

## 🎓 FOR NEW CONTRIBUTORS

### Getting Started
1. Read the Architecture Reference Manual
2. Review existing code style
3. Start with small fixes/docs
4. Ask questions in Discussions
5. Join the community!

### First Contribution Ideas
- Fix typos in documentation
- Add comments to complex code
- Write test cases
- Improve examples
- Translate documentation

---

## 📞 CONTACT

### Getting Help
- **GitHub Issues:** For bugs and feature requests
- **GitHub Discussions:** For questions and discussions
- **Maintainers:** Check MAINTAINERS.md

---

**Thank you for contributing to Origin-V Omega!**

*Together we build the future of sovereign computing.*
